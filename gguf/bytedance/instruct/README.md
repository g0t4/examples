# g0t4/ByteDance-Seed-Coder-8B-Instruct-GGUF

Based on https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Instruct

## GGUF Conversion

```sh
python convert_hf_to_gguf.py --remote ByteDance-Seed/Seed-Coder-8B-Instruct \
    --outtype f16 --outfile ByteDance-Seed-Coder-8B-Instruct-f16.gguf

./build/bin/llama-quantize ByteDance-Seed-Coder-8B-Instruct-f16.gguf ByteDance-Seed-Coder-8B-Instruct-Q8_0.gguf Q8_0
./build/bin/llama-quantize ByteDance-Seed-Coder-8B-Instruct-f16.gguf ByteDance-Seed-Coder-8B-Instruct-Q4_K_M.gguf Q4_K_M

hf upload ByteDance-Seed-Coder-8B-Instruct-GGUF .
```
