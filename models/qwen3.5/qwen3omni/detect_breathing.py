import torch
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info

# Load the model and processor
model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    # "Qwen/Qwen3-Omni-30B-A3B-Instruct",
    "Qwen/Qwen3-Omni-30B-A3B-Captioner",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2"
)

processor = Qwen3OmniMoeProcessor.from_pretrained("Qwen/Qwen3-Omni-30B-A3B-Instruct")

# %% 

# Define the conversation with the audio and a specific prompt
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "path/to/your/audio_clip.wav"},
            {"type": "text", "text": "Analyze this audio and determine if the sound of breathing is present. Respond with 'Breathing detected' or 'No breathing detected'."}
        ],
    }
]

# Prepare inputs
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversation, use_audio_in_video=False)
inputs = processor(
    text=text,
    audio=audios,
    return_tensors="pt",
    padding=True,
    use_audio_in_video=False
)
inputs = inputs.to(model.device).to(model.dtype)

# Generate response
output_ids = model.generate(**inputs, max_new_tokens=50)
output_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

# Print result
print("Analysis Result:", output_text)   
