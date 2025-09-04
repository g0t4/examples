# g0t4/ByteDance-Seed-Coder-8B-Reasoning-GGUF

Based on https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Reasoning-bf16
* Created from the bf16 variant of the reasonsing model (not the f32) *

## GGUF Conversion

```sh
python convert_hf_to_gguf.py --remote ByteDance-Seed/Seed-Coder-8B-Reasoning-bf16 \
    --outtype f16 --outfile ByteDance-Seed-Coder-8B-Reasoning-f16.gguf

llama-quantize ByteDance-Seed-Coder-8B-Reasoning-f16.gguf ByteDance-Seed-Coder-8B-Reasoning-Q4_K_M.gguf Q4_K_M
llama-quantize ByteDance-Seed-Coder-8B-Reasoning-f16.gguf ByteDance-Seed-Coder-8B-Reasoning-Q8_0.gguf Q8_0

hf upload ByteDance-Seed-Coder-8B-Reasoning-GGUF .
```
