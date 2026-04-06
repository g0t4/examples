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

# *** SUPER GOOD TRANSCRIPTION!

response = multimodal_generate(messages)
print(response)

# %%
#
import rich

def react_to(audio_file):
    # TODO! how about a system message to specify how to respond?
    classify = """This is a clip from a screencast. 
    You are helping me produce splits for video editing between demo segments, retakes, etc.
    I use algorithms to split up segments and then I need your help to double check the _AUDIO BETWEEN SEGMENTS_

    Please listen carefully to the contents of the audio. It could be any of the following:
    - A gasp or breathing like sound
    - Speaking is possible too though less likely
    - Keystroke(s) on a keyboard
    - Silence (no sounds, no breathing, no typing, etc)

    Which is it? Respond with one of the following only (nothing else): 
    - gasp
    - breathing
    - speaking
    - keystroke
    - silence

    """

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "audio",
                "audio": audio_file
            },
            {
                "type": "text",
                "text": classify,
            },
        ]
    }]
    rich.print(f'{audio_file}')
    return multimodal_generate(messages)

react_to("../qwen3omni/clips/clip10.wav")
react_to("../qwen3omni/clips/clip11.wav")
react_to("../qwen3omni/clips/clip20.wav")
react_to("../qwen3omni/clips/clip30.wav")
react_to("../qwen3omni/clips/clip40.wav")

# so far not reliably/repeatedly responding to the same audio file!
#  TODO is there carry over from prior audio inputs somehow? it almost seems like the first audio file + prompt effects subsequent?
#  TODO why does it randomly say it needs the audio (doesn't have it yet)?
#    the example on the HF repo said put audio first... I did audio first with Qwen3Omni too ...
#    oh well... for now lets stop!

# TODO! how about pass it he full video file so it can see any screen changes (if relevant?) ... maybe it would do better with sound with a bigger context of clip too? and ask what happened between talking times?
#
