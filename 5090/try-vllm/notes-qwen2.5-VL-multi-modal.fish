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
#    WOW TRHIS WAS FAST
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





# after the rebuild, install xformers w/o deps? OR find compatible build?
# LATER I s/b to get a custom cuda version like 12.6:
# pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu126
#
# BUT for 12.8 right now, that is only nightly so I can't use that for xformers (yet)
# pip3 install -U xformers --index-url https://download.pytorch.org/whl/nightly/cu128
#
# *** build xformers from src
git clone https://github.com/facebookresearch/xformers.git
# 
# CRAP, per GH issues the build fails?
#   https://github.com/facebookresearch/xformers/issues?q=is%3Aissue%20state%3Aopen%20%2012.8
# maybe just wait on using multimodal if this is required
#



