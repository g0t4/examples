# * autoreload changed modules (both `import` and `from` style imports)
import os

in_nvim_notebook = os.getenv("NVIM")
if in_nvim_notebook:
    get_ipython().extension_manager.load_extension("autoreload")  # pyright: ignore
    get_ipython().run_line_magic('autoreload', 'complete --print')  # pyright: ignore

import rich
# from rich.traceback import install
# install(show_locals=False)
from rich import print  # override default

from transformers import AutoModelForCausalLM, AutoTokenizer
# from transformers.models.qwen3_5 import Qwen3_5Tokenizer
# from transformers.models.qwen3_5_moe import ?

# %%

MODEL_ID = "Qwen/Qwen3.5-0.8B"
MODEL_ID = "Qwen/Qwen3.5-0.8B-Base"  # base model releases too! (i.e. for FIM)
# MODEL_ID = "Qwen/Qwen3.5-9B"
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

print(tokenizer)
print(model)

# %% 

rich.print(tokenizer.chat_template)  # rich makes the template legible!

# %%

prompt = "What is your name?"
conversation = [{"role": "user", "content": prompt}]
toks = tokenizer.apply_chat_template(
    conversation=conversation,
    add_generation_prompt=True,
    return_tensors="pt",
    enable_thinking=False,
)
toks = toks.to(model.device)

# TODO test flash-linear-attention speeds later (w/ and w/o on mac)

# uv add flash-linear-attention # TODO
