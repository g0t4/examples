#!/usr/bin/env python3
"""
Gemma-4-12B-IT multimodal audio examples.

Transcribes audio files and provides analysis/suggestions.

References:
  https://huggingface.co/google/gemma-4-12B
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from transformers import AutoModelForCausalLM, AutoProcessor


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_ID: str = "google/gemma-4-12B-it"
AUDIO_MAX_SECONDS: int = 30  # Gemma-4-12B audio limit

CLIPS_DIR: Path = Path(
    "/home/wes/repos/github/g0t4/examples/models/qwen3omni/clips"
)

SAMPLE1_WAV: Path = CLIPS_DIR / "editing_samples" / "sample1" / "sample1.wav"

# Target sample rate for audio input (Gemma expects 16kHz)
AUDIO_SAMPLE_RATE: int = 16000


# ---------------------------------------------------------------------------
# Helper: load model with best-effort GPU loading
# ---------------------------------------------------------------------------


def load_model_and_processor() -> tuple:
    """Load the Gemma-4-12B-IT model and its processor."""
    print(f"Loading processor from '{MODEL_ID}' ...", file=sys.stderr)
    processor = AutoProcessor.from_pretrained(MODEL_ID)

    print("Loading model (auto-detect device/dtype) ...", file=sys.stderr)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype="auto",
        device_map="auto",
    )
    return processor, model


# ---------------------------------------------------------------------------
# Load audio helper
# ---------------------------------------------------------------------------


def load_audio_as_waveform(audio_path: Path) -> np.ndarray:
    """Load an audio file and return a float32 numpy waveform array."""
    waveform, sr = librosa.load(audio_path, sr=AUDIO_SAMPLE_RATE)
    is_short_enough: bool = waveform.shape[0] <= AUDIO_MAX_SECONDS * AUDIO_SAMPLE_RATE
    if not is_short_enough:
        print(
            f"WARNING: {audio_path} is {waveform.shape[0] / sr:.1f}s "
            f"(max {AUDIO_MAX_SECONDS}s), truncating",
            file=sys.stderr,
        )
        waveform = waveform[: AUDIO_MAX_SECONDS * AUDIO_SAMPLE_RATE]
    return waveform


# ---------------------------------------------------------------------------
# Transcription with timestamps
# ---------------------------------------------------------------------------


def transcribe_with_timestamps(
    processor,
    model,
    audio_path: Path,
    max_new_tokens: int = 1024,
) -> dict[str, Any]:
    """Transcribe an audio file, requesting verbatim output with timestamps."""

    waveform: np.ndarray = load_audio_as_waveform(audio_path)

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Transcribe the following speech segment in its original "
                        "language into text. Follow these specific instructions for "
                        "formatting the answer:\n"
                        "* Output each segment with a start and end timestamp.\n"
                        "* When transcribing numbers, write the digits, "
                        "i.e. write 1.7 and not one point seven.\n"
                        "* Use the format: [START-END] transcript text\n"
                        "* Only output the transcription with timestamps."
                    ),
                },
                {"type": "audio", "audio": waveform},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
    ).to(model.device)

    input_len: int = inputs["input_ids"].shape[-1]

    print("  -> Generating transcription ...", file=sys.stderr)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=1.0,
        top_p=0.95,
        top_k=64,
    )

    raw_response: str = processor.decode(
        outputs[0][input_len:], skip_special_tokens=False
    )
    parsed: dict[str, Any] = processor.parse_response(raw_response)

    return {
        "audio_path": str(audio_path),
        "transcription": parsed.get("text", raw_response),
    }


# ---------------------------------------------------------------------------
# Follow-up analysis
# ---------------------------------------------------------------------------


def analyze_transcript_for_edits(
    processor,
    model,
    audio_path: Path,
    full_transcript: str,
    max_new_tokens: int = 1024,
) -> dict[str, Any]:
    """
    Ask the model to suggest edits, produce a clean transcript, and
    identify time ranges to keep/remove.
    """

    waveform: np.ndarray = load_audio_as_waveform(audio_path)

    transcript_text: str = (
        "Here is a transcription of an audio clip. Please provide:\n"
        "1. Suggested edits to improve the content (retakes edited out).\n"
        "2. A clean, final version of the transcript.\n"
        "3. Timestamp ranges to clip out (remove) and ranges to keep.\n\n"
        f"Transcript:\n{full_transcript}\n\n"
        "Format your answer clearly with numbered sections."
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": transcript_text},
                {"type": "audio", "audio": waveform},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
    ).to(model.device)

    input_len: int = inputs["input_ids"].shape[-1]

    print("  -> Generating edit suggestions ...", file=sys.stderr)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=1.0,
        top_p=0.95,
        top_k=64,
    )

    raw_response: str = processor.decode(
        outputs[0][input_len:], skip_special_tokens=False
    )
    parsed: dict[str, Any] = processor.parse_response(raw_response)

    return {
        "audio_path": str(audio_path),
        "full_transcript": full_transcript,
        "edit_analysis": parsed.get("text", raw_response),
    }


# ---------------------------------------------------------------------------
# Audio clip categorization
# ---------------------------------------------------------------------------


def categorize_audio_clips(
    processor,
    model,
    clip_paths: list[Path],
    max_new_tokens: int = 512,
) -> list[dict[str, Any]]:
    """Categorize each audio clip based on its content."""

    results: list[dict[str, Any]] = []

    for clip_path in clip_paths:
        waveform: np.ndarray = load_audio_as_waveform(clip_path)

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Listen to this audio clip and describe what is happening "
                            "in it. Categorize the content (e.g., music, speech, "
                            "ambient noise, sound effects). Be concise."
                        ),
                    },
                    {"type": "audio", "audio": waveform},
                ],
            }
        ]

        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
        ).to(model.device)

        input_len: int = inputs["input_ids"].shape[-1]

        print(f"  -> Categorizing {clip_path.name} ...", file=sys.stderr)
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
        )

        raw_response: str = processor.decode(
            outputs[0][input_len:], skip_special_tokens=False
        )
        parsed: dict[str, Any] = processor.parse_response(raw_response)

        results.append(
            {
                "clip_path": str(clip_path),
                "category": parsed.get("text", raw_response),
            }
        )

    return results


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gemma-4-12B-IT audio transcription & analysis"
    )
    parser.add_argument(
        "--task",
        choices=["transcribe", "analyze", "categorize", "all"],
        default="all",
        help="Which task(s) to run (default: all)",
    )
    parser.add_argument(
        "--clip",
        type=str,
        default=None,
        help="Path to a specific audio clip (overrides --clips-dir)",
    )
    parser.add_argument(
        "--clips-dir",
        type=str,
        default=str(CLIPS_DIR),
        help=f"Directory with clip files (default: {CLIPS_DIR})",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    processor, model = load_model_and_processor()

    # ------------------------------------------------------------------
    # Task: transcribe (sample1.wav)
    # ------------------------------------------------------------------
    if args.task in ("transcribe", "all"):
        print("=" * 70, file=sys.stderr)
        print("TASK: Transcribe sample1.wav with timestamps", file=sys.stderr)
        print("=" * 70, file=sys.stderr)

        if not SAMPLE1_WAV.exists():
            print(f"ERROR: {SAMPLE1_WAV} not found", file=sys.stderr)
            sys.exit(1)

        result = transcribe_with_timestamps(processor, model, SAMPLE1_WAV)
        print(f"\nTranscription:\n{result['transcription']}\n")
        print(
            f"Audio path: {result['audio_path']}",
            file=sys.stderr,
        )

        # ------------------------------------------------------------------
        # Task: analyze follow-up (if requested)
        # ------------------------------------------------------------------
        if args.task in ("analyze", "all"):
            print("=" * 70, file=sys.stderr)
            print("TASK: Analyze transcript for edits", file=sys.stderr)
            print("=" * 70, file=sys.stderr)

            analysis = analyze_transcript_for_edits(
                processor, model, SAMPLE1_WAV, result["transcription"]
            )
            print(f"\nEdit Analysis:\n{analysis['edit_analysis']}\n")

    # ------------------------------------------------------------------
    # Task: categorize clips
    # ------------------------------------------------------------------
    if args.task in ("categorize", "all"):
        print("=" * 70, file=sys.stderr)
        print("TASK: Categorize audio clips", file=sys.stderr)
        print("=" * 70, file=sys.stderr)

        clips_dir = Path(args.clips_dir)
        clip_files = sorted(clips_dir.glob("clip*.wav"))

        if not clip_files:
            print(f"No clip*.wav files found in {clips_dir}", file=sys.stderr)
        else:
            results = categorize_audio_clips(processor, model, clip_files)
            for r in results:
                print(f"  {Path(r['clip_path']).name}: {r['category']}")
            print()


# ---------------------------------------------------------------------------
# Allow running as module
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
