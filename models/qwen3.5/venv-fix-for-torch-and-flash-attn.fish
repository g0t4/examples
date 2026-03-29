#!/usr/bin/env fish

# *** torch==2.8.0 works!
uv sync # extras are now pip install'd next
uv pip install torch==2.8.0 flash-attn==2.8.3 einops==0.8.1

#     * test deps and/or get version info:
python3 -c "import torch; print(torch.version.cuda)"
# 12.8
python3 -c "import flash_attn; print('FlashAttention OK')"
# FlashAttention OK
