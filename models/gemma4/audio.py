from transformers import AutoProcessor, AutoModelForMultimodalLM

MODEL_ID = "google/gemma-4-E2B-it"

# Load model
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto", device_map="auto")

# %%

def multimodal_generate(messages: list[dict]) -> dict:
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

response = multimodal_generate(messages)
print(response)

# %%
#
import rich

def react_to(audio_file, instructions):
    content = [{"type": "audio", "audio": audio_file}]
    if instructions:
        content += [{"type": "text", "text": instructions}]

    conversation = [
        {
            "role": "user",
            "content": content,
        },
    ]
    rich.print(conversation)
    return multimodal_generate(conversation)

classify = """This is a clip from a screencast. 
You are helping me produce splits for video editing between demo segments, retakes, etc.
I use algorithms to split up segments and then I need your help to double check the audio between segments.
Please classify this clip as: speaking, keystroke(s), breathing, no sounds"""

react_to("../qwen3omni/clips/clip10.wav", classify)
react_to("../qwen3omni/clips/clip11.wav", classify)
react_to("../qwen3omni/clips/clip20.wav", classify)
react_to("../qwen3omni/clips/clip30.wav", classify)
react_to("../qwen3omni/clips/clip40.wav", classify)

# welp... gemma4 says "speaking" on all four :( ... did I do something wrong? 
