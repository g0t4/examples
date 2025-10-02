import torch
from transformers import Qwen3OmniMoeTalkerForConditionalGeneration, Qwen3OmniProcessor

def transcribe_audio_caption(audio_path: str, model_name: str = "Qwen/Qwen3-Omni-30B-A3B-Captioner"):
    # load model & processor
    model = Qwen3OmniMoeTalkerForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    processor = Qwen3OmniProcessor.from_pretrained(model_name)
    
    # load audio
    import soundfile as sf
    audio, sr = sf.read(audio_path)
    # (You might need to resample to 16k or the model’s expected rate)
    
    # build multimodal input with just audio
    inputs = processor(
        audio=audio,
        return_tensors="pt",
        sampling_rate=sr,
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    # generate caption / output text
    outputs = model.generate(**inputs, return_audio=False)
    
    # decode
    captions = processor.batch_decode(outputs, skip_special_tokens=True)
    return captions

if __name__ == "__main__":
    caps = transcribe_audio_caption("some_audio.wav")
    print(caps)
