"""Ask Kimi-Audio what it hears in one or more WAV files."""

import argparse
import os
from pathlib import Path

ROOT = Path(__file__ if "__file__" in globals().keys() else "").resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT / ".hf-cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import torch
from kimia_infer.api.kimia import KimiAudio


SAMPLING_PARAMS = {
    "audio_temperature": 0.8,
    "audio_top_k": 10,
    "text_temperature": 0.0,
    "text_top_k": 5,
    "audio_repetition_penalty": 1.0,
    "audio_repetition_window_size": 64,
    "text_repetition_penalty": 1.0,
    "text_repetition_window_size": 16,
}


model_path = "moonshotai/Kimi-Audio-7B-Instruct"

if not torch.cuda.is_available():
    raise SystemExit("Kimi-Audio requires a visible NVIDIA GPU.")

print(f"GPU: {torch.cuda.get_device_name(torch.cuda.current_device())}")
model = KimiAudio(model_path=model_path, load_detokenizer=False)

def analyze(prompt: str):
    # clips in current dir clip*.wav
    clips = [str(c) for c in Path().glob("*.wav")]
    for clip in sorted(clips):
        messages = [
            {"role": "user", "message_type": "text", "content": prompt },
            {"role": "user", "message_type": "audio", "content": str(clip)},
        ]
        _, answer = model.generate(messages, output_type="text", **SAMPLING_PARAMS)
        print(f"{clip}: {answer}")




analyze(prompt = "this is a clip from a screencast, briefly describe the sounds you hear")
#
# clip10.wav: a person is playing a drum set with a bass drum and a snare drum.
# clip11.wav: a person is playing a drum set with a bass drum and a snare drum.
# clip20.wav: Someone is typing on a keyboard.
# clip30.wav: a bell ringing
# clip40.wav: a person is speaking on a radio.
#
# not terrible! clip20/clip40 are correct!

# I bet if I give more context about likely sounds, or the ones I want to detect, it would do much better 
analyze(prompt = """this is a clip from a screencast, briefly describe the sounds you hear... here is a list of typical sounds (note this is not exhaustive, if you hear something else tell me!):
- speaking
- typing
- mouse clicks
- noticeable breathing (i.e. deep breathing)
- silence (mostly or entirely silent sections)

rare, but possible:
- laughing (or other audible emotions)
- microphone bump
- computer noises (i.e. alert noise)
- phone noises (i.e. ringing, message ding, alarms, etc)
""")
#
# hrmmmm... lol maybe not
# 
# clip10.wav: typing
# clip11.wav: typing
# clip20.wav: Typing
# clip30.wav: Silence
# clip40.wav: a person is speaking in a foreign language.


