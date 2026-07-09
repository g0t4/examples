#!/usr/bin/env fish

# https://huggingface.co/josefprusa/ThinkingCap-Qwen3.6-27B-int4-AutoRound-v1
set MODEL_ID josefprusa/ThinkingCap-Qwen3.6-27B-int4-AutoRound-v1

export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID

vllm serve "$MODEL_ID" \
  --dtype half \
  --max-model-len 262144 \
  --gpu-memory-utilization 0.92 \
  --kv-cache-dtype turboquant_4bit_nc \
  --max-num-seqs 16 \
  --max-num-batched-tokens 4096 \
  --enable-chunked-prefill \
  --max-long-partial-prefills 1 \
  --long-prefill-token-threshold 4096 \
  --compilation-config '{"cudagraph_mode":"PIECEWISE","cudagraph_capture_sizes":[1,2,3,4],"max_cudagraph_capture_size":4}' \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --default-chat-template-kwargs '{"enable_thinking":true,"preserve_thinking":true}' \
  --port 8012 \
  --host 0.0.0.0 \
  --trust-remote-code \
  --speculative-config '{"method":"mtp","num_speculative_tokens":1}'

