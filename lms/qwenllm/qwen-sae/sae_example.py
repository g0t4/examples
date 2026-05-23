# FYI copied from https://huggingface.co/Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50
#
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ── 1. Load base model ────────────────────────────────────────────────────────
model_name = "Qwen/Qwen3-8B-Base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
model.eval()

# ── 2. Load SAE for a target layer ───────────────────────────────────────────
# wget https://huggingface.co/Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50/resolve/main/layer30.sae.pt
LAYER = 30  # choose any layer in 0–35
sae = torch.load(f"layer{LAYER}.sae.pt", map_location="cuda")
W_enc = sae["W_enc"]  # (65536, 4096)
b_enc = sae["b_enc"]  # (65536,)

# %% 

def get_feature_acts(residual: torch.Tensor) -> torch.Tensor:
    """residual: (..., 4096) → sparse feature activations (..., 65536)"""
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts

# ── 3. Hook residual stream after the target transformer layer ────────────────
captured = {}

def _hook(module, input, output):
    hidden = output[0] if isinstance(output, tuple) else output
    captured["residual"] = hidden.detach().cuda()

hook = model.model.layers[LAYER].register_forward_hook(_hook)

# %% 

# ── 4. Forward pass ───────────────────────────────────────────────────────────
text = "The capital of France is"
inputs = tokenizer(text, return_tensors="pt")
with torch.no_grad():
    model(**inputs)
hook.remove()

# ── 5. Extract feature activations ───────────────────────────────────────────
residual = captured["residual"]               # (1, seq_len, 4096)
feature_acts = get_feature_acts(residual)     # (1, seq_len, 65536)

# Inspect active features for the last token
last_token_acts = feature_acts[0, -1]         # (65536,)
active_idx = last_token_acts.nonzero(as_tuple=True)[0]
print(f"Active features : {active_idx.tolist()}")
print(f"Feature values  : {last_token_acts[active_idx].tolist()}")
