# g0t4/ByteDance-Seed-Coder-8B-Base-GGUF

Based on https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Base

## GGUF Conversion

```sh
python convert_hf_to_gguf.py --remote ByteDance-Seed/Seed-Coder-8B-Base \
    --outtype f16 --outfile ByteDance-Seed-Coder-8B-Base-f16.gguf

llama-quantize ByteDance-Seed-Coder-8B-Base-f16.gguf ByteDance-Seed-Coder-8B-Base-Q4_K_M.gguf Q4_K_M
llama-quantize ByteDance-Seed-Coder-8B-Base-f16.gguf ByteDance-Seed-Coder-8B-Base-Q8_0.gguf Q8_0

hf upload ByteDance-Seed-Coder-8B-Base-GGUF .
```
