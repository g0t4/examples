
# links:
#   pytorch 5090 support:
#     https://github.com/pytorch/pytorch/issues/145949
#   vllm 5090 support:
#     https://github.com/vllm-project/vllm/issues/13306



# ***! next time try with ccache to speed up re-builds
sudo pacman --noconfirm -S ccache
#   https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html?device=cuda#full-build-with-compilation


# *** install pyenv for python versions
sudo pacman -S pyenv
pyenv install 3.12
#  NEXT time try using uv to run diff python versions
uv python list
uv venv -p python3.9 .venv # ** create new venv w/o any deps
# FYI can run python command too (though it complains if deps aren't satisifed)
#   uv run python --version # does this work even if pyproject.toml is present?
#   uv run --python 3.12 python --version


# * USE PYTHON 3.12 not 3.13
# FYI used pyenv to create a 3.12 venv (next time use uv above)
rm -rf .venv/
pyenv install 3.12
cd vllm/vllm repo dir
pyenv local 3.12.9
pyenv exec python -m venv .venv
# ** remove existing torch from requirements files:
pyenv exec python use_existing_torch.py
# activate venv:
source .venv/bin/activate.fish
python --version # confirm correct
# install compatible 12.8 nightly of pytorch:
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
# * GUIDE used for next custom build (didn't verbatim follow, but gist of it):
#   https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html?device=cuda#use-an-existing-pytorch-installation
# install deps to build vllm:
pip install  -r requirements/build.txt
pip install  -r requirements/common.txt
# *** WORKED to build vllm:
pip install -e . --no-build-isolation
#   FYI I had to install rust (used rustup pacman package) though I can't recall what dep needed that, I just got output from pip install that it was needed


# test it, it works!!!
vllm serve Qwen/Qwen2.5-7B-Instruct
# key output:
#
#   INFO 03-12 10:44:55 [worker.py:267] the current vLLM instance can use total_gpu_memory (31.37GiB) x gpu_memory_utilization (0.90) = 28.23GiB
#     if need be increase to > 90% gpu memory util?
#
#   INFO 03-12 10:44:46 [config.py:576] This model supports multiple tasks: {'score', 'classify', 'generate', 'embed', 'reward'}. Defaulting to 'generate'.
#   INFO 03-12 10:44:49 [config.py:576] This model supports multiple tasks: {'reward', 'classify', 'embed', 'generate', 'score'}. Defaulting to 'generate'.
#      TODO try other supported tasks!
#
#   TODO review more of output for the part that confirms loaded into GPU
#
# test completions:
curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
           "model": "Qwen/Qwen2.5-7B-Instruct",
           "messages": [{"role": "user", "content": "Hello!"}]
         }'

# DO NOT NEED MODEL in request, IIUC, b/c vllm serves one at a time (like llama-server)
curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
           "messages": [{"role": "user", "content": "Hello!"}]
         }'


