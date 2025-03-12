pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# issue tracking 5090 support:
# https://github.com/pytorch/pytorch/issues/145949
#

echo "
import torch
print(torch.cuda.is_available())  # True
print(torch.cuda.get_device_name(0))  # NVIDIA GeForce RTX 5090
print(torch.cuda.get_arch_list())
# ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120', 'compute_120']
" | uv run python


# vllm 5090 support:
#   https://github.com/vllm-project/vllm/issues/13306


