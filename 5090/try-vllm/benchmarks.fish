# 
# *** benchmark_serving.py
#   https://githubom/vllm-project/vllm/tree/main/benchmarks
#   remove access over HTTP API

nvidia-smi # ensure nothing is using gpu (memory)

set MODEL_NAME "Qwen/Qwen2.5-7B-Instruct"
vllm serve $MODEL_NAME --disable-log-requests
#
# new tab:
# get dataset:
cd benchmarks
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json

# missing packages that script needs:
pip install datasets pillow pandas

set NUM_PROMPTS 10
set BACKEND openai-chat
set DATASET_NAME sharegpt
set DATASET_PATH "ShareGPT_V3_unfiltered_cleaned_split.json"
python3 benchmark_serving.py --backend $BACKEND --model $MODEL_NAME \
    --endpoint /v1/chat/completions --dataset-name $DATASET_NAME \
    --dataset-path $DATASET_PATH --num-prompts $NUM_PROMPTS

# 295 tokens/sec output throughput!

# *** benchmark/throughput (offline):

# loads model inprocess (IIUC)

set MODEL_NAME "Qwen/Qwen2.5-7B-Instruct"
set NUM_PROMPTS 10
set DATASET_NAME sonnet
set DATASET_PATH "sonnet.txt"
python3 benchmark_throughput.py \
    --model "$MODEL_NAME" \
    --dataset-name "$DATASET_NAME" \
    --dataset-path "$DATASET_PATH" \
    --num-prompts "$NUM_PROMPTS"

# Throughput: 4.72 requests/s, 3262.58 total tokens/s, 708.33 output tokens/s
#   wtf 700 tokens/sec?!

# *** benchmark_prefix_caching.py
