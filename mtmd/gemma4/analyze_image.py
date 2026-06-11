"""
Submit an image to a multimodal llama.cpp server and ask it to identify what's in the image.
Tries port 8011 first, then falls back to port 8012.
"""

import base64
import json
import sys
from pathlib import Path
from typing import Optional

import requests


IMAGE_FILE = Path("image.png")
ENDPOINTS = [
    "http://ask.lan:8011",
    "http://ask.lan:8012",
]
SYSTEM_PROMPT = (
    "You are an image analysis assistant. "
    "Describe in detail what you see in the image, including objects, text, "
    "colors, layout, and any other relevant details."
)


def encode_image_to_base64(image_path: Path) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(image_path, "rb") as f:
        raw_bytes = f.read()
    return base64.b64encode(raw_bytes).decode("utf-8")


def submit_image_request(
    base_url: str,
    image_b64: str,
    prompt: str = "What is in this image?",
) -> Optional[dict]:
    """Send a multimodal chat completion request to the llama.cpp server."""
    url = f"{base_url}/v1/chat/completions"

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            },
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        return None


def main() -> None:
    if not IMAGE_FILE.exists():
        print(f"[ERROR] Image file not found: {IMAGE_FILE}", file=sys.stderr)
        sys.exit(1)

    image_b64 = encode_image_to_base64(IMAGE_FILE)
    print(f"Image encoded ({len(image_b64)} base64 chars)")

    for endpoint in ENDPOINTS:
        print(f"\nTrying {endpoint} ...")
        result = submit_image_request(endpoint, image_b64)

        if result is not None:
            try:
                choices = result["choices"]
                message = choices[0]["message"]["content"]
                print("\n--- Response ---")
                print(message)
                print("--- End ---\n")
                return
            except (KeyError, IndexError) as exc:
                print(f"  [ERROR] Unexpected response format: {exc}", file=sys.stderr)

    print("[ERROR] All endpoints failed.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
