# https://huggingface.co/zed-industries/zeta
#
vllm serve zed-industries/zeta --served-model-name zeta \
    --enable-prefix-caching --enable-chunked-prefill \
    --quantization="fp8" --speculative-model [ngram] \
        --ngram-prompt-lookup-max 4  \
    --ngram-prompt-lookup-min 2 \
        --num-speculative-tokens 8


