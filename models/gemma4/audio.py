from transformers import AutoProcessor, AutoModelForMultimodalLM

MODEL_ID = "google/gemma-4-E2B-it"

# Load model
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto", device_map="auto")

# %%

def transcribe_audio_message(messages: list[dict]) -> dict:
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
    ).to(model.device)
    input_len = inputs["input_ids"].shape[-1]

    outputs = model.generate(**inputs, max_new_tokens=512)
    response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
    return processor.parse_response(response)

# %% 

# Prompt - add audio before text
messages = [{
    "role": "user",
    "content": [
        {
            "type": "audio",
            "audio": "https://raw.githubusercontent.com/google-gemma/cookbook/refs/heads/main/Demos/sample-data/journal1.wav"
        },
        {
            "type": "text",
            "text": "Transcribe the following speech segment in its original language. Follow these specific instructions for formatting the answer:\n* Only output the transcription, with no newlines.\n* When transcribing numbers, write the digits, i.e. write 1.7 and not one point seven, and write 3 instead of three."
        },
    ]
}]

response = transcribe_audio_message(messages)
print(response)

# %% 

# ~/repos/github/g0t4/examples/models/qwen3omni/clips
