"""
Gemma 4 12B Unified - Multimodal capabilities demo.

Tests native audio transcription, categorization, and video editing assistance
using the encoder-free Gemma 4 12B model (supports text, image, audio).

Reference: https://huggingface.co/google/gemma-4-12B

Key best practices followed (per HF docs):
  - Audio content placed AFTER text in prompts
  - Standard sampling: temperature=1.0, top_p=0.95, top_k=64
  - Audio max 30 seconds length
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from transformers import AutoModelForMultimodalLM, AutoProcessor

console = Console()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_ID = "google/gemma-4-12B-it"

GENERATION_CONFIG: dict[str, Any] = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_new_tokens": 1024,
}

# Audio files to process (all < 30s limit per HF docs)
CLIPS_DIR = Path(__file__).resolve().parent.parent / "qwen3omni" / "clips"

EDITING_SAMPLE_PATH = CLIPS_DIR / "editing_samples" / "sample1" / "sample1.wav"
CLIP_FILES = sorted(CLIPS_DIR.glob("clip*.wav"))

console.print(f"[bold green]CLIPS_DIR:[/] {CLIPS_DIR}")
console.print(f"[bold green]MODEL_ID:[/] {MODEL_ID}")

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def load_model() -> tuple[AutoProcessor, AutoModelForMultimodalLM]:
    """Load the Gemma 4 12B model and processor."""
    console.print("[yellow]Loading model... this may take a moment.[/]")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForMultimodalLM.from_pretrained(
        MODEL_ID,
        dtype="auto",
        device_map="auto",
    )
    console.print("[bold green]✓ Model loaded.[/]")
    return processor, model


# Global model singleton
processor, model = load_model()

# ---------------------------------------------------------------------------
# Core inference
# ---------------------------------------------------------------------------


def generate_response(
    messages: list[dict],
    *,
    max_new_tokens: int | None = None,
    enable_thinking: bool = False,
) -> str:
    """Run inference on a message list and return the parsed response string.

    Follows Gemma 4 best practices:
      - Audio content placed AFTER text (per HF docs)
      - Standard sampling: temp=1.0, top_p=0.95, top_k=64
    """
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    ).to(model.device)

    input_len = inputs["input_ids"].shape[-1]

    gen_kwargs = dict(GENERATION_CONFIG)
    if max_new_tokens is not None:
        gen_kwargs["max_new_tokens"] = max_new_tokens

    outputs = model.generate(**inputs, **gen_kwargs)
    response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
    return processor.parse_response(response)


# ---------------------------------------------------------------------------
# Task 1: Verbatim transcription with timestamps
# ---------------------------------------------------------------------------

SYSTEM_TRANSCRIBE = (
    "You are a professional transcriptionist. "
    "Transcribe speech audio exactly as spoken, preserving all words, "
    "pauses, and verbal fillers."
)

TRANSCRIBE_PROMPT = (
    "Transcribe the following speech segment verbatim in its original language.\n"
    "\n"
    "Follow these specific formatting instructions:\n"
    "* Include approximate timestamps in [MM:SS] format at the start of each\n"
    "  spoken segment.\n"
    "* Only output the transcription with timestamps, no preamble or explanation.\n"
    "* Write numbers as digits (e.g. 1.7 not one point seven).\n"
    "* Preserve verbal stumbles, retakes, and false starts exactly as spoken."
)


def transcribe_with_timestamps(audio_path: Path) -> str:
    """Transcribe an audio file verbatim, requesting timestamp annotations."""
    messages = [
        {"role": "system", "content": SYSTEM_TRANSCRIBE},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": TRANSCRIBE_PROMPT},
                {"type": "audio", "audio": str(audio_path)},
            ],
        },
    ]
    return generate_response(messages, max_new_tokens=512)


# ---------------------------------------------------------------------------
# Task 2: Editing suggestions & retake detection
# ---------------------------------------------------------------------------

SYSTEM_EDITOR = (
    "You are a video editing assistant. "
    "Analyze the audio from a screencast tutorial and identify segments for removal "
    "(stumbles, retakes, dead air) to produce a clean final edit."
)

EDITING_PROMPT = (
    "You are reviewing a screencast recording. Identify verbal stumbles, "
    "retakes (where the speaker restarts a sentence), and unnecessary pauses.\n"
    "\n"
    "Please provide:\n"
    "1. A list of segments to REMOVE (with approximate time ranges) that contain\n"
    "   stumbles, retakes, or dead air.\n"
    "2. A clean edited transcript with ONLY the kept segments.\n"
    "3. The final time ranges to KEEP for the edited version.\n"
    "\n"
    "Format time ranges as [START to END] in seconds.\n"
)


def get_editing_suggestions(
    audio_path: Path,
    *,
    original_transcript: str | None = None,
) -> str:
    """Ask the model to identify retakes, suggest edits, and provide clip ranges."""
    text_parts = [EDITING_PROMPT]
    if original_transcript:
        text_parts.append(f"\n\nHere is the raw transcript for reference:\n---\n{original_transcript}\n---")

    messages = [
        {"role": "system", "content": SYSTEM_EDITOR},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "\n".join(text_parts)},
                {"type": "audio", "audio": str(audio_path)},
            ],
        },
    ]
    return generate_response(messages)


# ---------------------------------------------------------------------------
# Task 3: Audio clip categorization
# ---------------------------------------------------------------------------

CLIP_CATEGORIES: tuple[str, ...] = ("gasp", "breathing", "speaking", "keystroke", "silence")

CLASSIFY_SYSTEM = (
    "You are helping identify what kind of transition or gap audio represents "
    "between screencast segments."
)

CLASSIFY_PROMPT = (
    "This is a short clip from between screencast segments. "
    "Listen carefully and classify it as exactly ONE of the following:\n"
) + ", ".join(f"- {cat}" for cat in CLIP_CATEGORIES) + "\n\n" "Respond with only the category name (nothing else)."


def classify_clip(audio_path: Path) -> str:
    """Classify a short audio clip into a single category."""
    messages = [
        {"role": "system", "content": CLASSIFY_SYSTEM},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": CLASSIFY_PROMPT},
                {"type": "audio", "audio": str(audio_path)},
            ],
        },
    ]
    return generate_response(messages, max_new_tokens=32).strip().lower()


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------


def print_task_header(title: str, *, number: int) -> None:
    """Print a formatted section header."""
    console.print()
    console.print(Panel(f"[bold blue]Task {number}: {title}[/bold blue]", expand=False))
    console.print()


def print_result(label: str, text: str) -> None:
    """Print a labeled result in a panel."""
    console.print()
    console.print(Panel(Markdown(text), title=f"[bold]{label}[/bold]", expand=False))


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all demo tasks sequentially."""

    # ----- Task 1: Transcription -----
    print_task_header("Verbatim Transcription (with timestamps)", number=1)

    console.print(f"[dim]Audio file:[/] {EDITING_SAMPLE_PATH}")
    console.print(f"[dim]Duration check:[/] ", end="")

    # Verify audio is under 30s (Gemma 4 audio limit)
    import subprocess

    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(EDITING_SAMPLE_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        duration_secs = float(result.stdout.strip())
        duration_ok = duration_secs <= 30.0
        console.print(f"[green]✓[/] {duration_secs:.1f}s (under 30s limit)" if duration_ok else f"[red]✗[/] {duration_secs:.1f}s (EXCEEDS 30s limit!)")
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        console.print("[yellow]⚠ Could not verify duration (ffprobe not available)[/]")

    try:
        raw_transcript = transcribe_with_timestamps(EDITING_SAMPLE_PATH)
        print_result("Raw Transcript", raw_transcript)
    except Exception as exc:
        console.print(f"[red]Transcription failed:[/] {exc}")
        sys.exit(1)

    # ----- Task 2: Editing suggestions -----
    print_task_header("Editing Suggestions & Retake Detection", number=2)

    try:
        editing_suggestions = get_editing_suggestions(
            EDITING_SAMPLE_PATH,
            original_transcript=raw_transcript,
        )
        print_result("Editing Suggestions", editing_suggestions)
    except Exception as exc:
        console.print(f"[red]Editing suggestions failed:[/] {exc}")

    # ----- Task 3: Clip categorization -----
    print_task_header("Audio Clip Categorization", number=3)

    if not CLIP_FILES:
        console.print("[yellow]No clip*.wav files found.[/]")
        return

    table = Table(title="Clip Classification Results", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Category", style="bold")

    for clip_path in CLIP_FILES:
        try:
            category = classify_clip(clip_path)
            is_valid_category = category in CLIP_CATEGORIES
            if not is_valid_category:
                console.print(
                    f"  [yellow]⚠ '{clip_path.name}' → '{category}' "
                    f"(not in expected categories: {CLIP_CATEGORIES})[/]"
                )
        except Exception as exc:
            console.print(f"  [red]✗ {clip_path.name} failed:[/] {exc}")
            category = "ERROR"

        table.add_row(clip_path.name, category)

    console.print(table)

    # ----- Summary -----
    console.print()
    console.print("[dim]Done! Run again for fresh results (model stays loaded).[/]")


if __name__ == "__main__":
    main()
