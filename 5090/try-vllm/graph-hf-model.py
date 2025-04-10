import sys
import base64
from IPython.display import Image, display
from transformers import AutoModelForCausalLM, AutoModel, AutoTokenizer
from torchview import draw_graph
import torch
import torch.nn as nn

def show_image_iterm2(path):
    with open(path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode("ascii")
        print(f'\033]1337;File=inline=1;width=auto;height=auto;preserveAspectRatio=1:{b64}\a')

#%% 

# device='meta' -> no memory is consumed for visualization

# model_name = "meta-llama/Llama-3.2-1B-Instruct" # waiting for approval to gated
model_name ="Qwen/Qwen2.5-Coder-0.5B"
is_ipython = sys.argv[0].endswith("ipython")
if not is_python and len(sys.argv) > 1:
    model_name = sys.argv[1]
print(model_name)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

#%% 

from torchinfo import summary

# *** VERY NICE SUMMARY! (text and tree like)
model_stats = summary(model, input_size=(1, 32), dtypes= [ torch.long ] )  # batch size 1, seq len 32
print(model_stats)

#%% 

# write to model-graphs/ dir using model name santized
# model_graph = draw_graph(model, input_data=input_ids, expand_nested=True) 
file_name = model_name.replace('/', '-')
file_path = f"model-graphs/{file_name}.txt"
what = str(model_stats)
with open(file_path, 'wb') as f:
    f.write(what.encode('utf8'))


# OTHER TRIALS before using torchinfo which is all I really wanted (so far)

# #%% 
#
# from pprint import pprint
#
# from torch.fx import symbolic_trace
# pprint(dir(model))
#  inspect and dump info myself (IIAC enumerate module properties on each nested module)
#
# # Dummy input (batch size 1, sequence length 16)
# input_ids = tokenizer("def hello_world():\n    print('Hello, world!')", return_tensors="pt").input_ids
# traced = torch.jit.trace(model, input_ids)
# print(traced.graph)
#
#
#
# # traced = symbolic_trace(block)
# # # traced = symbolic_trace(model) # failed => code: co_varnames is too small
# # print(traced.graph)
#
# #%% 
# # Create and render the graph
# graph = draw_graph(model, input_data=input_ids, expand_nested=True)
#
# # model_graph = draw_graph(model, input_data=dummy_input, expand_nested=True) # device='meta'
#
# # well that sucks.. KeyError: '30213104720'
#
# fig = model_graph.visual_graph.render(format="png")
# display(Image(filename=fig, embed=True))
# show_image_iterm2(fig) # works in ipython directly, not when ipython is running in nvim
# # todo can I get it to work in nvim?
# #    appears to be a no?  
# #     https://github.com/wezterm/wezterm/issues/1163
# #     https://neovim.io/doc/user/terminal.html#terminal
