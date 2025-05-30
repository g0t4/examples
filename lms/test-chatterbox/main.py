import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

# model = ChatterboxTTS.from_pretrained(device="cuda")
model = ChatterboxTTS.from_pretrained(device="cpu")

text = "Ezreal and Jinx teamed up with Ahri, Yasuo, and Teemo to take down the enemy's Nexus in an epic late-game pentakill."
wav = model.generate(text)
ta.save("tmp/output/test1.wav", wav, model.sr)

print("doing me now")

# If you want to synthesize with a different voice, specify the audio prompt
AUDIO_PROMPT_PATH="tmp/part2-10s.wav"
wav = model.generate(text, audio_prompt_path=AUDIO_PROMPT_PATH)
ta.save("tmp/output/test1-me.wav", wav, model.sr)
