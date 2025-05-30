import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

model = ChatterboxTTS.from_pretrained(device="cuda")

# ** cpu notes (MUCH MUCH SLOWER like 30 seconds vs 1 second on mbp with m1 max)
# actually CPU works fine if you go in and modify torch.load calls to pass map_location="cpu"... even though they have .to(device) calls... that's not enough
#  go to this function:
#    https://github.com/g0t4/examples/blob/2aaa636/lms/test-chatterbox/.venv/lib/python3.12/site-packages/chatterbox/tts.py#L126
#    torch.load(ckpt_dir / "ve.pt", map_location="cpu")
#    and 4 more torch.loads after this (worked for me)... I did not verify why or which ones actually need it, just noting it worked
# model = ChatterboxTTS.from_pretrained(device="cpu")

# text = "Ezreal and Jinx teamed up with Ahri, Yasuo, and Teemo to take down the enemy's Nexus in an epic late-game pentakill."

text = "Let me tell you about chatterbox-tts, a python package wrapping a new model, based on llama 0.5B, that can take a reference audio file with your own voice, plus a text prompt, and it will generate an audio file with your voice speaking the text part, and it is fast with a CUDA device."
wav = model.generate(text)
ta.save("tmp/output/test3-01-stock-voice.wav", wav, model.sr)

AUDIO_PROMPT_PATH="tmp/my-voice-reference-10s.wav"
wav = model.generate(text, audio_prompt_path=AUDIO_PROMPT_PATH)
ta.save("tmp/output/test3-02-me-from-10s-clip.wav", wav, model.sr)

AUDIO_PROMPT_PATH="tmp/my-voice-reference-full.wav"
wav = model.generate(text, audio_prompt_path=AUDIO_PROMPT_PATH)
ta.save("tmp/output/test3-02-me-from-full-clip.wav", wav, model.sr)
