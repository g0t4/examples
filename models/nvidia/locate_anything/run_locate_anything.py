"""
LocateAnything-3B example: find the title text in thumb.png.

Runs on GPU 1 (second RTX 6000 Blackwell) to avoid interfering with
the llama-server on GPU 0.
"""

import re
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer, AutoProcessor


MODEL_PATH = "nvidia/LocateAnything-3B"
# GPU 1 is free; GPU 0 is running llama-server (~45GB)
DEVICE = "cuda:1"
DTYPE = torch.bfloat16
IMAGE_PATH = "thumb.png"
MAX_NEW_TOKENS = 8192


class LocateAnythingWorker:
    """Stateful worker that loads the model once and serves perception queries."""

    def __init__(self, model_path: str, device: str = "cuda", dtype: torch.dtype = torch.bfloat16):
        self.device = device
        self.dtype = dtype

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_path,
            dtype=dtype,
            trust_remote_code=True,
        ).to(device).eval()

    @torch.no_grad()
    def predict(
        self,
        image: Image.Image,
        question: str,
        generation_mode: str = "hybrid",
        max_new_tokens: int = 2048,
        temperature: float = 0.7,
        verbose: bool = True,
    ) -> dict:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": question},
                ],
            }
        ]

        text = self.processor.py_apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        images, videos = self.processor.process_vision_info(messages)
        inputs = self.processor(
            text=[text], images=images, videos=videos, return_tensors="pt"
        ).to(self.device)

        pixel_values = inputs["pixel_values"].to(self.dtype)
        input_ids = inputs["input_ids"]
        image_grid_hws = inputs.get("image_grid_hws", None)

        response = self.model.generate(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=inputs["attention_mask"],
            image_grid_hws=image_grid_hws,
            tokenizer=self.tokenizer,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            generation_mode=generation_mode,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1,
            verbose=verbose,
        )

        result = {"answer": response[0] if isinstance(response, tuple) else response}
        if isinstance(response, tuple) and len(response) >= 3:
            result["history"] = response[1]
            result["stats"] = response[2]
        return result

    @staticmethod
    def parse_boxes(answer: str, image_width: int, image_height: int) -> list[dict]:
        """Parse model output into pixel-coordinate bounding boxes.

        Coordinates in model output are normalized integers in [0, 1000].
        """
        boxes = []
        for match in re.finditer(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>", answer):
            x1, y1, x2, y2 = [int(group) for group in match.groups()]
            boxes.append(
                {
                    "x1": x1 / 1000 * image_width,
                    "y1": y1 / 1000 * image_height,
                    "x2": x2 / 1000 * image_width,
                    "y2": y2 / 1000 * image_height,
                }
            )
        return boxes

    @staticmethod
    def parse_points(answer: str, image_width: int, image_height: int) -> list[dict]:
        """Parse model output into pixel-coordinate points."""
        points = []
        for match in re.finditer(r"<box><(\d+)><(\d+)></box>", answer):
            x, y = int(match.group(1)), int(match.group(2))
            points.append(
                {
                    "x": x / 1000 * image_width,
                    "y": y / 1000 * image_height,
                }
            )
        return points


def draw_boxes_on_image(image: Image.Image, boxes: list[dict]) -> Image.Image:
    """Draw bounding boxes on an image for visualization."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)
    for box in boxes:
        draw.rectangle(
            [(box["x1"], box["y1"]), (box["x2"], box["y2"])],
            outline="red",
            width=5,
        )
    return image


def main():
    # Load the image
    image = Image.open(IMAGE_PATH).convert("RGB")
    image_width, image_height = image.size

    print(f"Image: {IMAGE_PATH} ({image_width}x{image_height})")
    print(f"Model: {MODEL_PATH}")
    print(f"Device: {DEVICE}")
    print(f"Memory on {DEVICE}: {torch.cuda.get_device_properties(1).total_memory / 1e9:.1f} GB total")
    print("-" * 60)

    # Load the model (this will take some time — it's 3B + vision encoder)
    print("Loading LocateAnything-3B model...")
    worker = LocateAnythingWorker(MODEL_PATH, device=DEVICE, dtype=DTYPE)
    print("Model loaded.")
    print("-" * 60)

    # Prompt: find the title (top-left, large 150pt font)
    prompt = "Locate the title text at the top-left of the image."
    print(f"Prompt: {prompt}")
    print("Generating... (this may take a minute)")
    print("-" * 60)

    result = worker.predict(
        image=image,
        question=prompt,
        generation_mode="hybrid",
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=0.7,
        verbose=True,
    )

    answer = result["answer"]
    print("-" * 60)
    print(f"Model answer:\n{answer}")
    print("-" * 60)

    # Parse bounding boxes
    boxes = LocateAnythingWorker.parse_boxes(answer, image_width, image_height)
    if boxes:
        print(f"Found {len(boxes)} bounding box(es):")
        for i, box in enumerate(boxes, 1):
            print(
                f"  Box {i}: "
                f"({box['x1']:.0f}, {box['y1']:.0f}) -> "
                f"({box['x2']:.0f}, {box['y2']:.0f})"
            )

        # Draw boxes and save
        annotated = image.copy()
        annotated = draw_boxes_on_image(annotated, boxes)
        output_path = "thumb_annotated.png"
        annotated.save(output_path)
        print(f"\nAnnotated image saved to: {output_path}")
    else:
        # Try parsing points as fallback
        points = LocateAnythingWorker.parse_points(answer, image_width, image_height)
        if points:
            print(f"Found {len(points)} point(s):")
            for i, pt in enumerate(points, 1):
                print(f"  Point {i}: ({pt['x']:.0f}, {pt['y']:.0f})")


if __name__ == "__main__":
    main()
