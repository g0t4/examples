#!/usr/bin/env fish

# * input variables
set upstream_org swiss-ai
set upstream_name Apertus-8B-2509
set outtype f16

# computed variables
set upstream $upstream_org/$upstream_name
set outfile $upstream_name-$outtype.gguf
set outfile_4 $upstream_name-Q4_K_M.gguf
set outfile_8 $upstream_name-Q8_0.gguf
set my_repo_name $upstream_name-GGUF

# * venv
source $HOME/repos/github/ggml-org/llama.cpp/.venv/bin/activate.fish

# * convert to GGUF
$HOME/repos/github/ggml-org/llama.cpp/.venv/bin/python3 \
    convert_hf_to_gguf.py \
    --remote $upstream \
    --outtype $outtype --outfile $outfile
#
# # * quantize
# llama-quantize $outfile \
#     $upstream_name-Q4_K_M.gguf Q4_K_M
# llama-quantize $outfile \
#     $upstream_name-Q8_0.gguf Q8_0
#
# # * README
# echo "
# # g0t4/$my_repo_name
#
# Based on https://huggingface.co/$upstream
#
# See [conversion script](./convert.fish)
# " >README.md
#
# # * upload gguf (and readme/scripts)
# hf repo create $my_repo_name
# hf upload $my_repo_name .
