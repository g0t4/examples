import base64
from IPython.display import Image, display
from transformers import AutoModel, AutoTokenizer
from torchview import draw_graph
import torch
import torch.nn as nn

# example: https://colab.research.google.com/github/mert-kurttutan/torchview/blob/main/docs/tutorial/notebook/example_introduction.ipynb#scrollTo=LQsuPp0ENRhY
#
class MLP(nn.Module):
    """Multi Layer Perceptron with inplace option.
    Make sure inplace=true and false has the same visual graph"""

    def __init__(self, inplace: bool = True) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(128, 128),
            nn.ReLU(inplace),
            nn.Linear(128, 128),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layers(x)
        return x

#%% 

def show_image_iterm2(path):
    with open(path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode("ascii")
        print(f'\033]1337;File=inline=1;width=auto;height=auto;preserveAspectRatio=1:{b64}\a')

model = MLP()
batch_size = 2
# device='meta' -> no memory is consumed for visualization
model_graph = draw_graph(model, input_size=(batch_size, 128), device='meta')
fig = model_graph.visual_graph.render(format="png")
display(Image(filename=fig, embed=True))
show_image_iterm2(fig) # works in ipython directly, not when ipython is running in nvim
# todo can I get it to work in nvim?
#    appears to be a no?  
#     https://github.com/wezterm/wezterm/issues/1163
#     https://neovim.io/doc/user/terminal.html#terminal
