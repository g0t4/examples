
git worktree add -b vllm-latest /home/wes/repos/github/vllm-project/vllm-latest origin/main 

python chat.py # my stupid simple chat client for demos
# prompt:    
#    tower of hanoi in lua!



curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "https://modelscope.oss-cn-beijing.aliyuncs.com/resource/qwen.png"}},
        {"type": "text", "text": "What is the text in the illustrate?"}
    ]}
    ]
    }'


vllm serve "Qwen/Qwen2.5-0.5B"
vllm serve "Qwen/Qwen2.5-0.5B-Instruct"
vllm serve "Qwen/Qwen2.5-7B-Instruct"

ls ~/.cache/huggingface/hub/
vllm serve "Qwen/Qwen2.5-3B-Instruct" # demo pulling 3B
vllm serve "Qwen/Qwen2.5-1.5B-Instruct" # demo pulling 3B
# https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct

curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{ "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "what is kotlin?" }
    ]}' | jq
