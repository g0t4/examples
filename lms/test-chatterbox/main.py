import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

model = ChatterboxTTS.from_pretrained(device="cuda")
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
