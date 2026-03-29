import torch
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info

# Load the model and processor
# MODEL_SLUG = "Qwen/Qwen3-Omni-30B-A3B-Instruct"
MODEL_SLUG = "Qwen/Qwen3-Omni-30B-A3B-Captioner"
model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    MODEL_SLUG,
    device_map="cuda:0",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
)

processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_SLUG)

# %%

conversation = [{
    "role": "user",
    "content": [
        {
            "type": "audio",
            "audio": "clip10.wav"
        },
        # {"type": "text", "text": "Analyze this audio and determine if the sound of breathing is present. Respond with 'Breathing detected' or 'No breathing detected'."}
        {
            "type": "text",
            "text": "Briefly describe this audio"
        }
    ],
}]

# Prepare inputs
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversation, use_audio_in_video=False)
inputs = processor(text=text, audio=audios, return_tensors="pt", padding=True, use_audio_in_video=False)
inputs = inputs.to(model.device).to(model.dtype)

# Generate response
output_ids = model.generate(**inputs, max_new_tokens=50)
output_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

# Print result
print("Analysis Result:", output_text)
