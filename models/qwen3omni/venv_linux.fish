#!/usr/bin/env fish

uv sync
# * got torch 2.8.0 working w/ flash-attn 2.8.3
uv pip install torch==2.8.0 torchvision==0.23 flash-attn==2.8.3
# see https://pypi.org/project/torchvision/ for torch/torchvision compat table
#   uv pip install torch==2.6.0 torchvision==0.21 flash-attn==2.8.3
#   uv pip install torch==2.7.0 torchvision==0.22 flash-attn==2.8.3
#   uv pip install torch==2.9.0 torchvision==0.24 flash-attn==2.8.3
#   uv pip install torch==2.10.0 torchvision==0.25 flash-attn==2.8.3
