import soundfile as sf
# Assuming the KimiAudio class is available after installation
from kimia_infer.api.kimia import KimiAudio
import torch # Ensure torch is imported if needed for device placement

# --- 1. Load Model ---
# Load the model from Hugging Face Hub
# Make sure you are logged in (`huggingface-cli login`) if the repo is private.
model_id = "moonshotai/Kimi-Audio-7B-Instruct" # Or "Kimi/Kimi-Audio-7B"
device = "cuda" if torch.cuda.is_available() else "cpu" # Example device placement
# Note: The KimiAudio class might handle model loading differently.
# You might need to pass the model_id directly or download checkpoints manually
# and provide the local path as shown in the original readme_kimia.md.
# Please refer to the main Kimi-Audio repository for precise loading instructions.
# Example assuming KimiAudio takes the HF ID or a local path:
try:
    model = KimiAudio(model_path=model_id, load_detokenizer=True) # May need device argument
    model.to(device) # Example device placement
except Exception as e:
    print(f"Automatic loading from HF Hub might require specific setup.")
    print(f"Refer to Kimi-Audio docs. Trying local path example (update path!). Error: {e}")
    # Fallback example:
    # model_path = "/path/to/your/downloaded/kimia-hf-ckpt" # IMPORTANT: Update this path if loading locally
    # model = KimiAudio(model_path=model_path, load_detokenizer=True)
    # model.to(device) # Example device placement

# --- 2. Define Sampling Parameters ---
sampling_params = {
    "audio_temperature": 0.8,
    "audio_top_k": 10,
    "text_temperature": 0.0,
    "text_top_k": 5,
    "audio_repetition_penalty": 1.0,
    "audio_repetition_window_size": 64,
    "text_repetition_penalty": 1.0,
    "text_repetition_window_size": 16,
}

# --- 3. Example 1: Audio-to-Text (ASR) ---
# TODO: Provide actual example audio files or URLs accessible to users
# E.g., download sample files first or use URLs
# wget https://path/to/your/asr_example.wav -O asr_example.wav
# wget https://path/to/your/qa_example.wav -O qa_example.wav
asr_audio_path = "asr_example.wav" # IMPORTANT: Make sure this file exists
qa_audio_path = "qa_example.wav" # IMPORTANT: Make sure this file exists

messages_asr = [
    {"role": "user", "message_type": "text", "content": "Please transcribe the following audio:"},
    {"role": "user", "message_type": "audio", "content": asr_audio_path}
]

# Generate only text output
# Note: Ensure the model object and generate method accept device placement if needed
_, text_output = model.generate(messages_asr, **sampling_params, output_type="text")
print(">>> ASR Output Text: ", text_output)
# Expected output: "这并不是告别，这是一个篇章的结束，也是新篇章的开始。" (Example)

# --- 4. Example 2: Audio-to-Audio/Text Conversation ---
messages_conversation = [
    {"role": "user", "message_type": "audio", "content": qa_audio_path}
]

# Generate both audio and text output
wav_output, text_output = model.generate(messages_conversation, **sampling_params, output_type="both")

# Save the generated audio
output_audio_path = "output_audio.wav"
# Ensure wav_output is on CPU and flattened before saving
sf.write(output_audio_path, wav_output.detach().cpu().view(-1).numpy(), 24000) # Assuming 24kHz output
print(f">>> Conversational Output Audio saved to: {output_audio_path}")
print(">>> Conversational Output Text: ", text_output)
# Expected output: "A." (Example)

print("Kimi-Audio inference examples complete.")
