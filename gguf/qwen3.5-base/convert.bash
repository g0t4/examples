#!/usr/bin/env bash
set -euo pipefail

TARGET=~/repos/github/g0t4/examples/gguf/qwen3.5-base
MODEL=$TARGET/models/Qwen3.5-35B-A3B-Base

cd ~/repos/github/ggml-org/llama.cpp 

hf download \
    Qwen/Qwen3.5-35B-A3B-Base \
    --local-dir "$TARGET/models/Qwen3.5-35B-A3B-Base"

python convert_hf_to_gguf.py \
    "$MODEL" \
    --outtype bf16 \
    --outfile "$TARGET/Qwen3.5-35B-A3B-Base-BF16.gguf"

./build/bin/llama-quantize \
    "$TARGET/Qwen3.5-35B-A3B-Base-BF16.gguf" \
    "$TARGET/Qwen3.5-35B-A3B-Base-Q8_0.gguf" \
    Q8_0
