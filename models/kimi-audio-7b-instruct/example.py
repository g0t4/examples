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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("clips", nargs="+", type=Path)
    parser.add_argument(
        "--prompt",
        default=(
            "Does this audio contain the sound of a human breathing? Answer "
            "exactly BREATHING or NOT BREATHING."
        ),
    )
    parser.add_argument("--model", default="moonshotai/Kimi-Audio-7B-Instruct")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("Kimi-Audio requires a visible NVIDIA GPU.")

    print(f"GPU: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    model = KimiAudio(model_path=args.model, load_detokenizer=False)
    for clip in args.clips:
        messages = [
            {"role": "user", "message_type": "text", "content": args.prompt},
            {"role": "user", "message_type": "audio", "content": str(clip)},
        ]
        _, answer = model.generate(messages, output_type="text", **SAMPLING_PARAMS)
        print(f"{clip}: {answer}")


if __name__ == "__main__":
    main()
