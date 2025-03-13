#  
# links:
#   https://docs.vllm.ai/en/latest/serving/multimodal_inputs.html
#   https://github.com/QwenLM/Qwen2.5-VL
#

source 
pip install xformers # derp this pooched my torch build... rebuilding it
# and it would've likely failed anyways b/c of compatiblity

# FML it failed and then decided to uninstall my custom pytorch build :(
# rebuilding now... 
#   I have ccache installed now... so, hopefully if I hit this issue again...
#     it will be faster to rebuild
# 
pip install -e . --no-build-isolation
# crap I forgot to put this back first:
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
# and this again:
pip install -e . --no-build-isolation
# PHEW fixed it for now :)
#
# ok cd to xformers checkout
# source .venv  
wcl https://github.com/facebookresearch/xformers.git
z xformers 
pip install --no-deps -e .
#    WOW THIS WAS FAST
#    --nodeps => or, do like vllm does and remove deps like torch from requirements.txt
#
# next just confirm non-multimodal model works:
vllm serve "Qwen/Qwen2.5-Coder-7B" # good!
#
# try this again:
vllm serve Qwen/Qwen2.5-VL-7B-Instruct
# cross fingers!
# CRAP OUT OF MEMORY!!! just barely!!!
# try 3B
vllm serve Qwen/Qwen2.5-VL-3B-Instruct
# ???
# ERROR 03-13 02:05:13 [engine.py:411] The model's max seq len (128000) is larger than the maximum number of tokens that can be stored in KV cache (3040). Try increasing `gpu_memory_utilization` or decreasing `max_model_len` when initializing the engine.
# dang... I need to decrease max_model_len
#    also basically KV cache was using 20GB of memory due to size!
vllm serve Qwen/Qwen2.5-VL-3B-Instruct --max-model-len 32768
#  and now the log shows:
#     INFO 03-13 02:07:41 [worker.py:267] model weights take 7.16GiB; non_torch_memory takes 0.12GiB; PyTorch activation peak memory takes 4.06GiB; the rest of the memory reserved for KV Cache is 16.90GiB.
#
#   YAY IT LOADED!
# TODO also change? 
# Using a slow image processor as `use_fast` is unset and a slow processor was saved with this model. `use_fast=True` will be the default behavior in v4.48, even if the model was saved with a slow processor. This will result in minor differences in outputs. You'll still be able to use a slow processor with `use_fast=False`.
# It looks like you are trying to rescale already rescaled images. If the input images have pixel values between 0 and 1, set `do_rescale=False` to avoid rescaling them again.

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
# OMFG! it works
# {"id":"chatcmpl-a1b7d248d39b4bf2974922972812a23b","object":"chat.completion","created":1741849891,"model":"Qwen/Qwen2.5-VL-3B-Instruct","choices":[{"index":0,"message":{"role":"assistant","reasoning_content":null,"content":"The text in the illustration reads \"TONGYI Qwen.\"","tool_calls":[]},"logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":{"prompt_tokens":74,"total_tokens":89,"completion_tokens":15,"prompt_tokens_details":null},"prompt_logprobs":null}⏎
#    => "content": "The text in the illustration reads \"TONGYI Qwen.\""

#
# FYI in the future, I should be able to find a build for cu128 once torch 12.8 moves to regular releases (not nightly server)
#   nightly serve doesn't list xformers wheel
# pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu128
#   FYI right now can get up to 12.6:
#      pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu126


