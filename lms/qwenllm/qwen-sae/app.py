"""
app.py — SAE Feature Explorer for Qwen3 models, whether pretrain (base) or posttrain (thinking/instruct) models.


this file is copied from https://huggingface.co/Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50/blob/main/app.py
    with a few parameter alterations (so far)

"""

import argparse
import html as _html
import json as _json
import os
from collections import OrderedDict

import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ─── CLI arguments ────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(description="SAE Feature Explorer")
_parser.add_argument(
    '--model',
    default='Qwen/Qwen3-8B',
    help='Path to the base model directory (default: %(default)s)',
)
_parser.add_argument(
    '--model-name-sae-trained-from',
    default='qwen3-8b-base',
    help='The name of model which present representations for SAE training (default: %(default)s)',
)
_parser.add_argument(
    '--model-name-analyzing-now',
    default='qwen3-8b',
    help='The name of model which is used for analyzing now (default: %(default)s)',
)
_parser.add_argument(
    '--sae-path',
    # FYI:     git clone https://huggingface.co/Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50
    default='SAE-Res-Qwen3-8B-Base-W64K-L0_50',
    help='Path to the directory containing layer*.sae.pt files (default: %(default)s)',
)
_parser.add_argument(
    '--top-k',
    type=int,
    default=50,
    help='Number of top features to display (default: %(default)s)',
)
_parser.add_argument(
    '--num-layers',
    type=int,
    default=36,
    help='Number of transformer layers in the model (default: %(default)s)',
)
_parser.add_argument(
    '--sae-width',
    type=int,
    default=65_536,
    help='SAE dictionary width / number of features (default: %(default)s)',
)
_parser.add_argument(
    '--d-model',
    type=int,
    default=4096,
    help='Model hidden dimension (default: %(default)s)',
)
_parser.add_argument(
    '--sae-cache-max',
    type=int,
    default=8, # TODO
    help='Maximum number of SAE layers to keep in memory at once (default: %(default)s)',
)
_parser.add_argument(
    '--server-port',
    type=int,
    default=7860,
    help='Port number for server',
)
_args = _parser.parse_args()

# ─── Config ──────────────────────────────────────────────────────────────────
MODEL_PATH                  = _args.model
MODEL_NAME_SAE_TRAINED_FROM = _args.model_name_sae_trained_from
MODEL_NAME_ANALYZING_NOW    = _args.model_name_analyzing_now
SAE_PATH                    = _args.sae_path
TOP_K                       = _args.top_k
NUM_LAYERS                  = _args.num_layers
SAE_WIDTH                   = _args.sae_width
D_MODEL                     = _args.d_model
SAE_CACHE_MAX               = _args.sae_cache_max
PORT                        = _args.server_port

# ─── Generation defaults (from model's generation_config.json) ────────────────

_gen_cfg: dict = {}
_gen_cfg_path = os.path.join(MODEL_PATH, 'generation_config.json')
if os.path.exists(_gen_cfg_path):
    with open(_gen_cfg_path) as _f:
        _gen_cfg = _json.load(_f)
    print(f"Loaded generation_config.json from {_gen_cfg_path}")
else:
    print(f"No generation_config.json found at {_gen_cfg_path}; using built-in defaults.")

GEN_DO_SAMPLE    = bool(_gen_cfg.get('do_sample',           False))
GEN_TEMPERATURE  = float(_gen_cfg.get('temperature',        1.0))
GEN_TOP_P        = float(_gen_cfg.get('top_p',              1.0))
GEN_TOP_K        = int(_gen_cfg.get('top_k',                1))
GEN_REP_PENALTY  = float(_gen_cfg.get('repetition_penalty', 1.0))
STEER_DISPLAY_K  = 10   # top-k candidates shown in the per-token probability panel

# ─── Default chat templates (thinking / no-thinking) ─────────────────────────

_THINK_TEMPLATE = (
    "<|im_start|>user\n"
    "{content}"
    "<|im_end|>\n"
    "<|im_start|>assistant\n"
    "<think>\n"
)

_NOTHINK_TEMPLATE = (
    "<|im_start|>user\n"
    "{content}"
    "<|im_end|>\n"
    "<|im_start|>assistant\n"
    "<think>\n\n</think>\n\n"
)

def apply_default_template(prompt: str, think: bool) -> str:
    """Wrap *prompt* in the ChatML template for thinking or no-thinking mode."""
    tpl = _THINK_TEMPLATE if think else _NOTHINK_TEMPLATE
    return tpl.format(content=prompt.strip())

# ─── Device resolution ───────────────────────────────────────────────────────

def _resolve_sae_device() -> torch.device:
    """
    Pick the device for SAE weights and encoder/decoder computations.

    CUDA_VISIBLE_DEVICES remaps physical GPUs so that the first listed GPU
    always appears as cuda:0 inside this process.  We simply use cuda:0
    when any CUDA device is visible; fall back to CPU otherwise.
    """
    if not torch.cuda.is_available():
        print("SAE device: cpu  (no CUDA visible)")
        return torch.device('cpu')
    cvd = os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')
    device = torch.device('cuda:0')
    print(f"SAE device: {device} — {torch.cuda.get_device_name(device)}"
          f"  [CUDA_VISIBLE_DEVICES={cvd}]")
    return device

SAE_DEVICE = _resolve_sae_device()

# ─── Global singletons ───────────────────────────────────────────────────────
_model     = None
_tokenizer = None
_sae_lru: OrderedDict = OrderedDict()
_orig_cache: dict | None = None   # cached unsteered generation result


def get_model():
    global _model, _tokenizer
    if _model is None:
        print("Loading model…")
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, device_map='auto', torch_dtype='auto'
        )
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        _model.eval()
        print("Model ready.")
    return _model, _tokenizer


def get_sae(layer: int) -> dict:
    if layer in _sae_lru:
        _sae_lru.move_to_end(layer)
        return _sae_lru[layer]
    if len(_sae_lru) >= SAE_CACHE_MAX:
        _sae_lru.popitem(last=False)
    path = os.path.join(SAE_PATH, f'layer{layer}.sae.pt')
    try:
        sae = torch.load(path, map_location=SAE_DEVICE, weights_only=True)
    except TypeError:
        sae = torch.load(path, map_location=SAE_DEVICE)
    # Pre-convert and transpose encoder weights once on load so compute_sae_features
    # never repeats the conversion on every call.
    sae['_W_enc'] = sae['W_enc'].T.to(dtype=torch.float32)  # [d_model, sae_width]
    sae['_b_enc'] = sae['b_enc'].to(dtype=torch.float32)      # [sae_width]
    _sae_lru[layer] = sae
    return sae


# ─── Core math ───────────────────────────────────────────────────────────────

def topk_relu(x: torch.Tensor, k: int = TOP_K) -> torch.Tensor:
    # Scatter top-k ReLU values directly — avoids creating a full-size boolean mask
    # and an element-wise multiply, saving two [seq, SAE_WIDTH] allocations.
    relu_x = torch.relu(x)
    values, indices = torch.topk(relu_x, k, dim=-1)
    out = torch.zeros_like(relu_x)
    out.scatter_(-1, indices, values)
    return out


@torch.no_grad()
def capture_hidden(model, input_ids: torch.Tensor, layer: int) -> torch.Tensor:
    buf = {}
    def _hook(module, inp, out):
        # Qwen3MoE decoder layers return a plain tensor [batch, seq, hidden].
        # out[0] removes the batch dim → [seq, hidden]; then move to SAE_DEVICE.
        buf['h'] = out[0].detach().to(SAE_DEVICE, dtype=torch.float32)
    handle = model.model.layers[layer].register_forward_hook(_hook)
    model(input_ids)
    handle.remove()
    return buf['h']   # [seq_len, d_model]


@torch.no_grad()
def capture_all_hiddens(model, input_ids: torch.Tensor, layers: list) -> dict:
    """
    Capture residual-stream hidden states at multiple layers in a single
    forward pass by registering simultaneous hooks.  Tensors are stored on
    SAE_DEVICE as float32 so downstream SAE matmuls need no extra transfer.
    """
    buf = {}
    handles = []
    for layer in layers:
        def make_hook(l):
            def _hook(module, inp, out):
                buf[l] = out[0].detach().to(SAE_DEVICE, dtype=torch.float32)
            return _hook
        handles.append(model.model.layers[layer].register_forward_hook(make_hook(layer)))
    model(input_ids)
    for h in handles:
        h.remove()
    return buf  # {layer_idx: Tensor[seq, d_model] on SAE_DEVICE}


def compute_sae_features(hidden: torch.Tensor, sae: dict,
                         raw: bool = False) -> torch.Tensor:
    # Use pre-converted weights cached on load (avoids .float()/.T on every call)
    W_enc = sae['_W_enc']   # [d_model, sae_width] float32 on SAE_DEVICE
    b_enc = sae['_b_enc']   # [sae_width] float32 on SAE_DEVICE
    pre   = hidden @ W_enc + b_enc            # [seq, sae_width] — pre-activation on SAE_DEVICE
    if raw:
        return pre                            # keep negative values intact; caller handles device
    return topk_relu(pre, TOP_K)              # stays on SAE_DEVICE; caller calls .tolist() as needed


# ─── UI helpers ──────────────────────────────────────────────────────────────


def parse_positions(s: str):
    """
    Parse a position string into 'all' or a sorted list of int indices.

    Supported syntax (comma-separated, combinable):
      all        → every token position
      5          → single position
      3-7        → inclusive range (positions 3, 4, 5, 6, 7)
      0,2,5-8    → mix of individual positions and ranges
    """
    s = s.strip().lower()
    if s == 'all':
        return 'all'
    try:
        positions: list[int] = []
        for part in s.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                lo, hi = part.split('-', 1)
                positions.extend(range(int(lo.strip()), int(hi.strip()) + 1))
            else:
                positions.append(int(part))
        return sorted(set(positions))
    except Exception:
        return 'all'


def feature_heatmap_to_html(tokens: list, features: torch.Tensor, top_k: int, skip_first: bool = False) -> str:
    """
    Build a 2-D HTML heatmap:
      rows  = top-k features (ranked by mean activation across all positions)
      cols  = token positions
      color = activation value (white → red, normalised per feature row by row max)
    """

    seq_len, sae_width = features.shape
    top_k = min(int(top_k), sae_width)

    # ── Optionally exclude the first token ────────────────────────────────────
    if skip_first and seq_len > 1:
        features = features[1:]
        tokens   = tokens[1:]
        seq_len -= 1

    # ── Select top-k features by mean activation across all positions ─────────
    mean_per_feat = features.mean(dim=0)                # [sae_width]
    top_vals, top_idx = torch.topk(mean_per_feat, top_k)
    feat_acts = features[:, top_idx]                    # [seq_len, top_k]

    # ── Token column headers ──────────────────────────────────────────────────
    TH_STYLE = (
        "min-width:38px;max-width:70px;padding:4px 3px;"
        "text-align:center;font-weight:500;font-size:11px;"
        "color:#444;border-bottom:2px solid #c7d2e8;"
        "overflow:hidden;white-space:nowrap;vertical-align:bottom;"
    )
    tok_headers = []
    for i, tok in enumerate(tokens):
        raw   = tok.strip() or f"[{i}]"
        short = _html.escape(raw[:6] + "…" if len(raw) > 6 else raw)
        full  = _html.escape(raw)
        tok_headers.append(
            f'<th style="{TH_STYLE}" title="pos {i}: {full}">{short}</th>'
        )

    # ── Data rows ─────────────────────────────────────────────────────────────
    FEAT_TD  = (
        "font-family:ui-monospace,monospace;font-size:11px;"
        "padding:3px 8px;color:#2563eb;white-space:nowrap;"
        "border-right:2px solid #c7d2e8;background:#f8faff;"
        "position:sticky;left:0;z-index:1;"
    )
    AVG_TD   = (
        "font-size:10px;padding:3px 6px;color:#777;white-space:nowrap;"
        "border-right:1px solid #e4e7ef;text-align:right;"
    )
    CELL_BASE = (
        "border:1px solid rgba(0,0,0,0.05);min-width:38px;height:30px;"
        "text-align:center;vertical-align:middle;"
    )

    rows_html = []
    for fi in range(top_k):
        feat_i  = int(top_idx[fi])
        avg_val = float(top_vals[fi])
        row_acts = feat_acts[:, fi]             # [seq_len]
        row_max  = float(row_acts.max())
        norm     = row_max if row_max > 0 else 1.0

        cells = []
        for pos in range(seq_len):
            v = float(row_acts[pos])
            t = max(0.0, min(1.0, v / norm))
            # white → amber → deep red
            r = 255
            g = int(255 * (1 - 0.8 * t))
            b = int(255 * (1 - t))
            cells.append(
                f'<td style="{CELL_BASE}background:rgb({r},{g},{b});"'
                f' title="feat #{feat_i} | pos {pos} | act={v:.4f}">'
                f'</td>'
            )

        rows_html.append(
            f'<tr>'
            f'<td style="{FEAT_TD}">#{feat_i}</td>'
            f'<td style="{AVG_TD}">{avg_val:.3f}</td>'
            + "".join(cells)
            + "</tr>"
        )

    # ── Assemble table ────────────────────────────────────────────────────────
    header_row = (
        '<tr>'
        '<th style="padding:4px 8px;text-align:left;font-size:11px;font-weight:700;'
        'color:#2563eb;border-bottom:2px solid #c7d2e8;border-right:2px solid #c7d2e8;'
        'background:#f8faff;position:sticky;left:0;z-index:2;">Feature</th>'
        '<th style="padding:4px 6px;font-size:11px;font-weight:700;color:#777;'
        'border-bottom:2px solid #c7d2e8;border-right:1px solid #e4e7ef;">'
        'Avg&nbsp;act.</th>'
        + "".join(tok_headers)
        + "</tr>"
    )

    legend = (
        '<div style="display:flex;align-items:center;gap:10px;margin-top:10px;'
        'font-size:11px;color:#888;">'
        '<span>0</span>'
        '<div style="width:140px;height:12px;border-radius:6px;'
        'background:linear-gradient(to right,#fff,#ff6600,#cc0000);'
        'border:1px solid #ddd;"></div>'
        '<span>peak activation (per-feature row-max scale)</span>'
        '</div>'
    )

    return (
        '<div style="overflow-x:auto;max-height:520px;overflow-y:auto;">'
        '<table style="border-collapse:collapse;width:100%;'
        'font-family:ui-monospace,monospace;">'
        f'<thead style="position:sticky;top:0;background:#fff;z-index:3;">'
        f'{header_row}</thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table>'
        '</div>'
        + legend
    )


def tokens_with_positions_html(tokens: list, positions) -> str:
    """
    Render tokenized prompt as coloured token chips.

    Steered positions (amber/gold) are visually distinct from unsteered ones (grey).
    positions: 'all'  →  every index is highlighted
               list   →  only those indices
    """

    if not tokens:
        return (
            '<div style="padding:10px;color:#bbb;font-size:13px;">'
            'Enter a prompt above to preview token positions.</div>'
        )

    all_positions = positions if isinstance(positions, list) else []
    pos_set = (
        set(range(len(tokens))) if positions == 'all'
        else {p for p in all_positions if 0 <= p < len(tokens)}
    )
    # Positions beyond the prompt — will be steered in the generated text
    generated_positions = (
        [] if positions == 'all'
        else sorted(p for p in all_positions if p >= len(tokens))
    )

    parts = []
    for i, tok in enumerate(tokens):
        steered = i in pos_set
        txt   = _html.escape(tok)
        title = _html.escape(repr(tok.strip()), quote=True)

        if steered:
            bg, border, text_color = "#fef3c7", "2px solid #f59e0b", "#92400e"
        else:
            bg, border, text_color = "#f1f5f9", "1px solid #e2e8f0", "#475569"

        parts.append(
            f'<span style="background:{bg};color:{text_color};'
            f'padding:3px 7px;margin:2px 1px;border-radius:5px;'
            f'display:inline-block;border:{border};'
            f'font-family:ui-monospace,monospace;font-size:12px;" '
            f'title="pos {i}: {title}">'
            f'<sub style="opacity:.55;font-size:9px;margin-right:2px">{i}</sub>'
            f'{txt}</span>'
        )

    n_steered = len(pos_set)
    summary = (
        f'<div style="margin-top:6px;font-size:11px;color:#888;">'
        f'{len(tokens)}&nbsp;tokens total&nbsp;&nbsp;·&nbsp;&nbsp;'
        f'<span style="color:#92400e;font-weight:600;">{n_steered}&nbsp;steered</span>'
        f'&nbsp;<span style="color:#f59e0b;">■</span>'
        f'</div>'
    )

    generated_note = ''
    if generated_positions:
        gp_str = ', '.join(str(p) for p in generated_positions)
        generated_note = (
            f'<div style="margin-top:4px;font-size:11px;padding:4px 8px;'
            f'background:#eff6ff;border:1px solid #bfdbfe;border-radius:4px;color:#1d4ed8;">'
            f'Positions {gp_str} are beyond the prompt — they will be steered '
            f'in the <em>generated</em> text during autoregressive decoding.'
            f'</div>'
        )

    return (
        '<div style="padding:8px 4px;line-height:2.8;">'
        + ' '.join(parts)
        + summary
        + generated_note
        + '</div>'
    )


def cb_feature_heatmap(state, top_k: int, skip_first: bool):
    if state is None:
        return (
            '<div style="min-height:80px;display:flex;align-items:center;'
            'justify-content:center;color:#bbb;font-size:13px;">'
            'Run analysis first to see the feature heatmap.</div>'
        )
    tokens, features = state
    return feature_heatmap_to_html(tokens, features, int(top_k), bool(skip_first))


# ─── Gradio callbacks ────────────────────────────────────────────────────────

def cb_analyze(text: str, layer: int):
    try:
        model, tokenizer = get_model()
        input_ids = tokenizer.encode(text, return_tensors='pt').to(
            next(model.parameters()).device
        )
        tokens   = [tokenizer.decode([t]) for t in input_ids[0].tolist()]
        hidden   = capture_hidden(model, input_ids, int(layer))
        features = compute_sae_features(hidden, get_sae(int(layer)))
        return (tokens, features)
    except Exception as e:
        raise gr.Error(f"Analysis failed: {e}")



def _steering_strength_from_mode(mode: str, diff_lookup, layer: int, feat_idx: int,
                                  custom_val: float = 5.0) -> float:
    """Map Light/Medium/Strong/Custom to an actual steering strength.

    Looks up the feature-specific diff for (layer, feat_idx) from the
    Feature Comparison results.  Falls back to the global max across all
    compared features, then to fixed defaults when no data is available.
    """
    if mode == "Custom":
        return float(custom_val)
    d = 0.0
    if diff_lookup and isinstance(diff_lookup, dict):
        key = (int(layer), int(feat_idx))
        if key in diff_lookup:
            d = float(diff_lookup[key])
        else:
            d = float(max(diff_lookup.values(), default=0.0))
    if d <= 0:
        return {"Light": 5.0, "Medium": 20.0, "Strong": 100.0}.get(mode, 5.0)
    return {"Light": round(d * 0.5, 2),
            "Medium": round(d * 2.0, 2),
            "Strong": round(d * 10.0, 2)}.get(mode, round(d, 2))


def cb_generate(prompt, layer, feat_idx, pos_str, steer_mode, compare_diff,
                steer_output_only, max_tok, greedy, top_k_tok, top_p, rep_penalty, temp,
                custom_strength=5.0, apply_think=False, apply_nothink=False):
    try:
        return _cb_generate_inner(prompt, layer, feat_idx, pos_str, steer_mode, compare_diff,
                                  steer_output_only, max_tok, greedy, top_k_tok, top_p, rep_penalty, temp,
                                  custom_strength, apply_think, apply_nothink)
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"Generation failed: {e}")


def cb_update_steer_preview(prompt: str, pos_str: str,
                             apply_think: bool = False, apply_nothink: bool = False):
    """Tokenise the prompt and return an HTML token-position preview."""
    if not prompt.strip():
        return (
            '<div style="padding:10px;color:#bbb;font-size:13px;">'
            'Enter a prompt above to preview steered positions.</div>'
        )
    try:
        _, tokenizer = get_model()
        if apply_think:
            effective = apply_default_template(prompt, think=True)
        elif apply_nothink:
            effective = apply_default_template(prompt, think=False)
        else:
            effective = prompt
        input_ids = tokenizer.encode(effective)
        tokens    = [tokenizer.decode([t]) for t in input_ids]
        positions = parse_positions(pos_str)
        return tokens_with_positions_html(tokens, positions)
    except Exception as e:
        return (
            f'<div style="padding:10px;color:#dc2626;font-size:13px;">'
            f'Preview error: {e}</div>'
        )


def _extract_probs(gen_out, input_len: int, tokenizer, display_k: int):
    """
    Extract per-step token probabilities from a `return_dict_in_generate=True,
    output_scores=True` GenerateOutput.

    Returns (text, tokens, chosen_probs, topk_data) where:
      tokens       : list[str]  — decoded token strings
      chosen_probs : list[float] — probability of the chosen token (0-1)
      topk_data    : list[list[[str, float, bool]]] — top-k candidates at each step,
                     each entry is [token_str, prob, is_chosen]
    """
    new_ids     = gen_out.sequences[0][input_len:]
    new_id_list = new_ids.tolist()

    # Batch-decode chosen tokens and all top-k candidates in two passes
    # instead of O(n * display_k) individual tokenizer.decode() calls.
    all_topk_ids: list[list[int]] = []
    chosen_probs: list[float]     = []
    topk_vals_list: list          = []
    chosen_in_top_list: list[bool]= []

    for score_t, tok_id in zip(gen_out.scores, new_id_list):
        probs              = torch.softmax(score_t[0].float(), dim=-1)
        chosen_probs.append(float(probs[tok_id]))
        top_vals, top_ids  = torch.topk(probs, display_k)
        tid_list           = top_ids.tolist()
        chosen_in_top      = tok_id in tid_list
        all_topk_ids.append(tid_list)
        topk_vals_list.append(top_vals.tolist())
        chosen_in_top_list.append(chosen_in_top)

    # Single batch_decode call for all chosen tokens
    tokens: list[str] = tokenizer.batch_decode(
        [[t] for t in new_id_list], skip_special_tokens=False
    )

    # Single batch_decode call for all top-k candidate tokens
    flat_ids      = [tid for ids in all_topk_ids for tid in ids]
    flat_decoded  = tokenizer.batch_decode(
        [[t] for t in flat_ids], skip_special_tokens=False
    )

    topk_data = []
    flat_idx  = 0
    for i, (tok_id, ids, vals, chosen_in_top, chosen_prob) in enumerate(
        zip(new_id_list, all_topk_ids, topk_vals_list, chosen_in_top_list, chosen_probs)
    ):
        entry = []
        for tid, tv in zip(ids, vals):
            entry.append([flat_decoded[flat_idx], tv, tid == tok_id])
            flat_idx += 1
        if not chosen_in_top:
            entry.append([tokens[i], chosen_prob, True])
        topk_data.append(entry)

    text = tokenizer.decode(new_ids, skip_special_tokens=True)
    return text, tokens, chosen_probs, topk_data


def probs_to_html(tokens: list, chosen_probs: list, topk_data: list,
                  panel_id: str, theme: str = 'blue') -> str:
    """
    Render per-token generation probabilities as coloured chips.
    Clicking a chip pins its top-k candidate table in the panel below;
    clicking the same chip again or another chip toggles/switches the display.
    Scroll-stable: no hover events that fire on page scroll.

    theme: 'blue' for original output, 'red' for steered output.
    """

    if not tokens:
        return ('<div style="padding:10px;color:#bbb;font-size:13px;">'
                'No tokens generated.</div>')

    # ── Chip colour (white → saturated) based on probability ─────────────────
    def _colors(prob: float):
        t = max(0.0, min(1.0, prob))
        if theme == 'blue':
            r, g, b = int(255 * (1 - t * 0.85)), int(255 * (1 - t * 0.65)), 255
            txt = '#1e3a8a' if t < 0.55 else '#ffffff'
        else:
            r, g, b = 255, int(255 * (1 - t * 0.82)), int(255 * (1 - t))
            txt = '#7f1d1d' if t < 0.55 else '#ffffff'
        return f'rgb({r},{g},{b})', txt

    # ── Pre-build the top-k panel HTML in Python ──────────────────────────────
    TH = 'padding:2px 8px;font-size:11px;color:#6b7280;border-bottom:1px solid #e4e7ef;'

    def _panel_html(entry: list) -> str:
        rows = []
        for rank, (tok_str, prob, is_chosen) in enumerate(entry, 1):
            bg = 'background:#dbeafe;' if is_chosen else ''
            fw = 'font-weight:700;'    if is_chosen else ''
            mk = ' ✓'                  if is_chosen else ''
            rows.append(
                f'<tr style="border-bottom:1px solid #f4f6ff;{bg}">'
                f'<td style="padding:2px 8px;text-align:right;font-size:11px;color:#9ca3af;">{rank}</td>'
                f'<td style="padding:2px 8px;font-family:monospace;font-size:12px;{fw}">{_html.escape(tok_str)}{mk}</td>'
                f'<td style="padding:2px 8px;text-align:right;font-family:monospace;font-size:12px;">{prob:.4f}</td>'
                f'<td style="padding:2px 8px;text-align:right;font-family:monospace;font-size:12px;">{prob * 100:.2f}%</td>'
                f'</tr>'
            )
        return (
            '<table style="border-collapse:collapse;width:100%;font-size:12px;">'
            f'<thead style="background:#f8faff;"><tr>'
            f'<th style="{TH}text-align:right;">Rank</th>'
            f'<th style="{TH}text-align:left;">Token</th>'
            f'<th style="{TH}text-align:right;">Prob</th>'
            f'<th style="{TH}text-align:right;">%</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody>'
            '</table>'
        )

    # ── Inline JS — click to pin, click again to unpin ───────────────────────
    # Uses data-prob-root to scope sibling chips without global IDs.
    # Single-quoted JS string literals are safe inside double-quoted HTML attrs.
    # Non-f-string parts: { } are literal characters (no f-string substitution).
    JS_CLICK = (
        "var root=this.closest('[data-prob-root]');"
        "if(!root)return;"
        "var p=root.querySelector('[data-topk-panel]');"
        "if(!p)return;"
        "var sel=this.dataset.selected==='1';"
        "root.querySelectorAll('[data-chip]').forEach(function(e){"
        "e.dataset.selected='0';e.style.outline='';});"
        "if(sel){"
        "p.innerHTML='';p.style.display='none';"
        "}else{"
        "this.dataset.selected='1';"
        "this.style.outline='2px solid #94a3b8';"
        "this.style.outlineOffset='-1px';"
        "p.innerHTML=this.getAttribute('data-panel');"
        "p.style.display='block';"
        "}"
    )

    def _tok_disp(s: str) -> str:
        return s.replace('\n', '↵').replace('\r', '↵').replace('\t', '→')

    # ── Build chips ───────────────────────────────────────────────────────────
    chips = []
    for tok, prob, entry in zip(tokens, chosen_probs, topk_data):
        bg, txt = _colors(prob)
        panel_attr = _html.escape(_panel_html(entry), quote=True)
        chips.append(
            f'<span data-chip data-selected="0" '
            f'style="background:{bg};color:{txt};padding:3px 8px 2px;margin:1px;'
            f'border-radius:5px;display:inline-block;cursor:pointer;white-space:nowrap;'
            f'font-family:ui-monospace,monospace;font-size:12px;" '
            f'data-panel="{panel_attr}" '
            f'onclick="{JS_CLICK}">'
            f'{_html.escape(_tok_disp(tok))}'
            f'<sub style="opacity:.75;font-size:9px;margin-left:3px;">{prob * 100:.1f}%</sub>'
            f'</span>'
        )

    return (
        '<div data-prob-root style="padding:2px;">'
        '<div style="font-size:11px;color:#888;margin-bottom:6px;font-style:italic;">'
        'Click a token to pin its top-k candidates &nbsp;·&nbsp; click again to dismiss.</div>'
        '<div style="padding:4px;line-height:2.8;">'
        + ''.join(chips)
        + '</div>'
        + '<div data-topk-panel style="display:none;margin-top:8px;padding:4px;'
          'background:#f8faff;border:1px solid #e4e7ef;border-radius:6px;'
          'max-height:220px;overflow-y:auto;"></div>'
        + '</div>'
    )


def _cb_generate_inner(prompt, layer, feat_idx, pos_str, steer_mode, compare_diff,
                       steer_output_only, max_tok, greedy, top_k_tok, top_p, rep_penalty, temp,
                       custom_strength=5.0, apply_think=False, apply_nothink=False):
    global _orig_cache
    model, tokenizer = get_model()
    layer    = int(layer)
    feat_idx = int(feat_idx)
    if not (0 <= feat_idx < SAE_WIDTH):
        raise gr.Error(f"Feature index must be in [0, {SAE_WIDTH - 1}].")
    strength  = _steering_strength_from_mode(steer_mode, compare_diff, layer, feat_idx, float(custom_strength))
    positions = parse_positions(pos_str)

    if apply_think:
        effective_prompt = apply_default_template(prompt, think=True)
    elif apply_nothink:
        effective_prompt = apply_default_template(prompt, think=False)
    else:
        effective_prompt = prompt
    input_ids = tokenizer.encode(effective_prompt, return_tensors='pt').to(
        next(model.parameters()).device
    )

    # Build generation kwargs shared by both calls
    gen_kwargs: dict = dict(max_new_tokens=int(max_tok),
                            return_dict_in_generate=True, output_scores=True)
    if greedy:
        gen_kwargs['do_sample'] = False
    else:
        gen_kwargs['do_sample']              = True
        gen_kwargs['temperature']            = float(temp)
        gen_kwargs['top_k']                  = int(top_k_tok)
        gen_kwargs['top_p']                  = float(top_p)
        gen_kwargs['repetition_penalty']     = float(rep_penalty)

    prompt_len = input_ids.shape[1]

    # ── Original generation (cached) ─────────────────────────────────────────
    # The unsteered output depends only on the prompt and decoding parameters,
    # not on any steering inputs.  Reuse the last result when those are unchanged.
    if greedy:
        orig_key = (effective_prompt, int(max_tok), True)
    else:
        orig_key = (effective_prompt, int(max_tok), False,
                    int(top_k_tok), float(top_p), float(rep_penalty), float(temp))

    if _orig_cache is not None and _orig_cache['key'] == orig_key:
        orig_text       = _orig_cache['text']
        orig_probs_html = _orig_cache['probs_html']
    else:
        with torch.no_grad():
            orig_out = model.generate(input_ids, **gen_kwargs)
        orig_text, orig_toks, orig_probs, orig_topk = _extract_probs(
            orig_out, prompt_len, tokenizer, STEER_DISPLAY_K
        )
        orig_probs_html = probs_to_html(orig_toks, orig_probs, orig_topk,
                                        'topk-panel-orig', theme='blue')
        _orig_cache = dict(key=orig_key, text=orig_text, probs_html=orig_probs_html)

    sae          = get_sae(layer)
    steering_vec = sae['W_dec'][:, feat_idx].float()   # [d_model]
    pos_set      = None if positions == 'all' else set(positions)
    counter      = [0]

    def _steer_hook(module, inp, out):
        # out: plain tensor [batch, seq, hidden] for Qwen3MoE
        h           = out.clone()
        sv          = steering_vec.to(device=h.device, dtype=h.dtype)  # one fused transfer
        cur_counter = counter[0]
        counter[0] += 1
        if cur_counter == 0:
            # Prefill: apply position-based steering to the prompt
            if positions == 'all':
                h = h + strength * sv
            else:
                for p in positions:
                    if 0 <= p < h.shape[1]:
                        h[:, p, :] = h[:, p, :] + strength * sv
        else:
            # Decode step (KV-cache): h is [batch, 1, hidden]
            # Steer if: output-only mode is on, positions='all', or this position is listed
            cur_seq_pos = prompt_len + cur_counter - 1
            if steer_output_only or positions == 'all' or cur_seq_pos in pos_set:
                h[:, 0, :] = h[:, 0, :] + strength * sv
        return h

    handle = model.model.layers[layer].register_forward_hook(_steer_hook)
    with torch.no_grad():
        steer_out = model.generate(input_ids, **gen_kwargs)
    handle.remove()
    steer_text, steer_toks, steer_probs, steer_topk = _extract_probs(
        steer_out, prompt_len, tokenizer, STEER_DISPLAY_K
    )

    steer_probs_html = probs_to_html(steer_toks, steer_probs, steer_topk,
                                     'topk-panel-steer', theme='red')

    return orig_text, steer_text, orig_probs_html, steer_probs_html



# ─── Feature Comparison helpers ──────────────────────────────────────────────

def compare_to_html(records: list, text1: str, text2: str,
                    tokens1: list = None, tokens2: list = None) -> tuple:
    """
    Render comparison results as two HTML strings:
      - tok_display_html: token rows for the left panel (data-tok-display root)
      - feature_table_html: feature table for the right panel

    Returns (tok_display_html, feature_table_html).
    """

    _TOK_PLACEHOLDER = (
        '<div style="min-height:60px;display:flex;align-items:center;'
        'justify-content:center;color:#bbb;font-size:13px;padding:8px;">'
        'Run Compare to see token activations here.</div>'
    )

    if not records:
        return (
            _TOK_PLACEHOLDER,
            '<div style="min-height:80px;display:flex;align-items:center;'
            'justify-content:center;color:#bbb;font-size:13px;">'
            'No results — try a wider layer range or larger Top-K.</div>',
        )

    # ── Token display blocks ──────────────────────────────────────────────────
    TOK_SPAN = (
        "display:inline-block;padding:3px 7px;margin:2px 1px;"
        "border-radius:5px;font-family:ui-monospace,monospace;font-size:12px;"
        "background:#eef2ff;color:#374151;cursor:default;"
        "transition:background .1s;border:1px solid rgba(0,0,0,0.06);"
    )

    def render_tok_row(tokens, seq_id):
        parts = []
        for i, tok in enumerate(tokens):
            txt   = _html.escape(tok)
            title = _html.escape(repr(tok.strip()), quote=True)
            parts.append(
                f'<span data-seq={seq_id} data-pos={i} style="{TOK_SPAN}" '
                f'title="pos {i}: {title}">'
                f'<sub style="opacity:.5;font-size:9px;margin-right:2px">{i}</sub>'
                f'{txt}</span>'
            )
        return " ".join(parts)

    # Build token display HTML for the left panel
    if tokens1 and tokens2:
        tok_inner = (
            '<div style="margin-bottom:10px;color:#1e293b;">'
            '<div style="font-size:11px;font-weight:700;color:#2563eb;'
            'text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px;">'
            f'Example 1 &nbsp;<span style="font-weight:400;color:#888;">'
            f'({len(tokens1)} tokens)</span></div>'
            '<div style="line-height:2.8;padding:8px 10px;background:#fafbff;'
            'border-radius:8px;border:1px solid #e4e7ef;overflow-x:auto;">'
            + render_tok_row(tokens1, 1)
            + '</div></div>'
            '<div style="margin-bottom:8px;color:#1e293b;">'
            '<div style="font-size:11px;font-weight:700;color:#dc2626;'
            'text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px;">'
            f'Example 2 &nbsp;<span style="font-weight:400;color:#888;">'
            f'({len(tokens2)} tokens)</span></div>'
            '<div style="line-height:2.8;padding:8px 10px;background:#fafbff;'
            'border-radius:8px;border:1px solid #e4e7ef;overflow-x:auto;">'
            + render_tok_row(tokens2, 2)
            + '</div></div>'
            '<div style="font-size:11px;color:#888;font-style:italic;">'
            'Hover a feature row on the right to highlight activations.</div>'
        )
    else:
        tok_inner = _TOK_PLACEHOLDER

    # Wrap with data-tok-display so the JS hover handler can find it across columns
    tok_display_html = f'<div data-tok-display style="padding:2px;">{tok_inner}</div>'

    # ── Per-layer max for bar-width normalization ─────────────────────────────
    _layer_max: dict = {}
    for _d, _l, *_ in records:
        if _d > _layer_max.get(_l, 0.0):
            _layer_max[_l] = _d

    # ── Inline JS snippets for hover-highlight ────────────────────────────────
    # Uses document.querySelector('[data-tok-display]') so the handler works
    # across Gradio columns (token panel on left, feature table on right).
    _JS_ENTER = (
        "var d=document.querySelector('[data-tok-display]');"
        "if(!d)return;"
        "var a1=JSON.parse(this.getAttribute('data-acts1'));"
        "var a2=JSON.parse(this.getAttribute('data-acts2'));"
        "if(!a1||!a2)return;"
        "var pk=Math.max.apply(null,a1.map(Math.abs).concat(a2.map(Math.abs)))||0.0001;"
        "function c1(v){var t=Math.abs(v)/pk;"
        "return 'rgb('+Math.round(255*(1-t))+','+Math.round(255*(1-.6*t))+',255)'}"
        "function c2(v){var t=Math.abs(v)/pk;"
        "return 'rgb(255,'+Math.round(255*(1-.8*t))+','+Math.round(255*(1-t))+')'}"
        "d.querySelectorAll('[data-seq]').forEach(function(e){"
        "var s=e.dataset.seq,p=parseInt(e.dataset.pos,10);"
        "if(s==='1'&&p<a1.length)e.style.background=c1(a1[p]);"
        "else if(s==='2'&&p<a2.length)e.style.background=c2(a2[p]);});"
        "this.style.outline='2px solid #94a3b8';"
        "this.style.outlineOffset='-1px';"
    )
    _JS_LEAVE = (
        "var d=document.querySelector('[data-tok-display]');"
        "if(!d)return;"
        "d.querySelectorAll('[data-seq]').forEach(function(e){e.style.background='';});"
        "this.style.outline='';"
    )

    TR_BASE = "border-bottom:1px solid #f0f4ff;"
    TH = (
        "padding:6px 10px;font-size:11px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:.5px;white-space:nowrap;"
    )

    rows_html = []
    current_layer = None
    layer_rank = 0
    for _rank, record in enumerate(records, 1):
        diff_val, layer, feat_idx, act1, act2 = record[:5]
        acts1_pos = record[5] if len(record) > 5 else None
        acts2_pos = record[6] if len(record) > 6 else None

        # Insert a layer-group header row whenever the layer changes
        if layer != current_layer:
            current_layer = layer
            layer_rank = 0
            rows_html.append(
                f'<tr style="background:#eef2ff;border-top:2px solid #c7d2e8;">'
                f'<td colspan="6" style="padding:4px 12px;font-size:11px;font-weight:700;'
                f'color:#2563eb;letter-spacing:.5px;">Layer {layer}</td>'
                f'</tr>'
            )
        layer_rank += 1

        bar_w = max(2, int(120 * diff_val / (_layer_max.get(layer) or 1.0)))
        if act1 >= act2:
            bar_color = "#2563eb"
            dir_label = "Ex&nbsp;1&nbsp;▲"
            dir_color = "#2563eb"
            row_bg    = "background:#f5f8ff;"
        else:
            bar_color = "#dc2626"
            dir_label = "Ex&nbsp;2&nbsp;▲"
            dir_color = "#dc2626"
            row_bg    = "background:#fff5f5;"

        # Embed per-position activation arrays for the hover handler
        if acts1_pos is not None and acts2_pos is not None:
            a1_json = _json.dumps(acts1_pos)
            a2_json = _json.dumps(acts2_pos)
            tr_open = (
                f"<tr style='{TR_BASE}{row_bg}cursor:pointer;'"
                f" data-acts1='{a1_json}'"
                f" data-acts2='{a2_json}'"
                f' onmouseenter="{_JS_ENTER}"'
                f' onmouseleave="{_JS_LEAVE}">'
            )
        else:
            tr_open = f'<tr style="{TR_BASE}{row_bg}">'

        rows_html.append(
            tr_open
            + f'<td style="padding:5px 10px;text-align:center;color:#9ca3af;font-size:11px;">{layer_rank}</td>'
            + f'<td style="padding:5px 10px;font-family:monospace;color:#2563eb;">#{feat_idx}</td>'
            + f'<td style="padding:5px 8px;text-align:right;font-family:monospace;color:#374151;">{act1:.1%}</td>'
            + f'<td style="padding:5px 8px;text-align:right;font-family:monospace;color:#374151;">{act2:.1%}</td>'
            + f'<td style="padding:5px 10px;">'
            +  f'  <div style="display:flex;align-items:center;gap:6px;">'
            +  f'    <div style="width:{bar_w}px;height:10px;background:{bar_color};'
            +  f'         border-radius:3px;flex-shrink:0;"></div>'
            +  f'    <span style="font-family:monospace;font-size:12px;color:#374151;">{diff_val:.1%}</span>'
            +  f'  </div>'
            + f'</td>'
            + f'<td style="padding:5px 10px;font-size:11px;font-weight:700;color:{dir_color};">'
            + f'{dir_label}</td>'
            + '</tr>'
        )

    ex1_short = _html.escape(text1[:50] + "…" if len(text1) > 50 else text1)
    ex2_short = _html.escape(text2[:50] + "…" if len(text2) > 50 else text2)

    legend = (
        '<div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;'
        'font-size:11px;color:#6b7280;">'
        f'<span><span style="color:#2563eb;font-weight:700;">■ Ex 1</span>'
        f' "{ex1_short}"</span>'
        f'<span><span style="color:#dc2626;font-weight:700;">■ Ex 2</span>'
        f' "{ex2_short}"</span>'
        '</div>'
    )

    table_inner = (
        '<div style="overflow-x:auto;max-height:560px;overflow-y:auto;color:#1e293b;">'
        '<table style="border-collapse:collapse;width:100%;color:#1e293b;'
        'font-family:ui-monospace,monospace;font-size:13px;">'
        '<thead style="background:#f8faff;color:#1e293b;border-bottom:2px solid #c7d2e8;'
        'position:sticky;top:0;z-index:2;">'
        '<tr>'
        f'<th style="{TH}color:#9ca3af;">Rank</th>'
        f'<th style="{TH}color:#2563eb;">Feature</th>'
        f'<th style="{TH}color:#2563eb;text-align:right;">Rate&nbsp;Ex&nbsp;1</th>'
        f'<th style="{TH}color:#dc2626;text-align:right;">Rate&nbsp;Ex&nbsp;2</th>'
        f'<th style="{TH}color:#6b7280;">|Rate diff|</th>'
        f'<th style="{TH}color:#6b7280;">Higher</th>'
        '</tr>'
        '</thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table>'
        '</div>'
    )

    feature_table_html = (
        '<div style="padding:2px;">'
        + table_inner
        + legend
        + '</div>'
    )

    return tok_display_html, feature_table_html


def cb_compare(text1: str, text2: str, layer_from: int, layer_to: int,
               top_k: int, skip_first: bool,
               remove_common_toks: bool, remove_prefix: bool,
               raw_acts: bool = False):
    try:
        if not text1.strip() or not text2.strip():
            raise gr.Error("Both examples must be non-empty.")

        model, tokenizer = get_model()
        layer_from = int(layer_from)
        layer_to   = int(layer_to)
        top_k      = int(top_k)
        if layer_from > layer_to:
            layer_from, layer_to = layer_to, layer_from
        layers = list(range(layer_from, layer_to + 1))

        # ── Tokenise ─────────────────────────────────────────────────────────
        model_dev = next(model.parameters()).device
        ids1 = tokenizer.encode(text1, return_tensors='pt').to(model_dev)
        ids2 = tokenizer.encode(text2, return_tensors='pt').to(model_dev)
        toks1 = ids1[0].tolist()
        toks2 = ids2[0].tolist()

        # ── Build per-sequence keep-index lists ───────────────────────────────
        prefix_len = 0
        if remove_prefix:
            for a, b in zip(toks1, toks2):
                if a == b:
                    prefix_len += 1
                else:
                    break

        common_tok_ids: set = set()
        if remove_common_toks:
            common_tok_ids = set(toks1) & set(toks2)

        def _build_keep(toks: list) -> list:
            return [
                i for i, t in enumerate(toks)
                if not (skip_first and i == 0)
                and i >= prefix_len
                and t not in common_tok_ids
            ]

        keep1 = _build_keep(toks1)
        keep2 = _build_keep(toks2)

        # ── Capture hidden states for all layers in two forward passes ────────
        hiddens1 = capture_all_hiddens(model, ids1, layers)
        hiddens2 = capture_all_hiddens(model, ids2, layers)

        # Decoded token strings for the HTML token display
        tokens1_str = [tokenizer.decode([t]) for t in toks1]
        tokens2_str = [tokenizer.decode([t]) for t in toks2]

        # ── Per-layer feature activation-rate difference ──────────────────────
        # Activation rate = fraction of kept positions where the feature fires
        # (activation > 0).  Ranking by |rate1 − rate2| highlights features
        # that are selectively active in one example but not the other.
        # Load one SAE at a time to avoid OOM (each SAE is ~1-2 GB on GPU).
        candidates = []   # (abs_diff, layer, feat_idx, rate1, rate2,
                          #  acts1_per_pos, acts2_per_pos)
        for layer in layers:
            sae = get_sae(layer)

            # Full per-position feature activations — stay on SAE_DEVICE for GPU math
            feats1 = compute_sae_features(hiddens1[layer], sae, raw=raw_acts)  # [seq1_len, SAE_WIDTH]
            feats2 = compute_sae_features(hiddens2[layer], sae, raw=raw_acts)  # [seq2_len, SAE_WIDTH]

            # Activation rate = fraction of kept positions where feature fires (> 0)
            def _rate(feats: torch.Tensor, keep_idx: list) -> torch.Tensor:
                if not keep_idx:
                    return torch.zeros(feats.shape[1], device=feats.device, dtype=feats.dtype)
                return (feats[keep_idx] > 0).float().mean(dim=0)

            r1   = _rate(feats1, keep1)
            r2   = _rate(feats2, keep2)
            diff = (r1 - r2).abs()

            # Top-k per layer (all kept — no global trim)
            local_k    = min(top_k, SAE_WIDTH)
            vals, idxs = torch.topk(diff, local_k)
            for v, fi in zip(vals.tolist(), idxs.tolist()):
                # Round to 3 dp — enough precision for color interpolation
                a1_pos = [round(x, 3) for x in feats1[:, fi].tolist()]
                a2_pos = [round(x, 3) for x in feats2[:, fi].tolist()]
                candidates.append((v, layer, fi, float(r1[fi]), float(r2[fi]),
                                   a1_pos, a2_pos))

            # Free SAE weights and feature tensors before loading the next layer
            del sae, feats1, feats2, diff

        # Single cache clear after all layers — calling it per-layer is expensive
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # ── Per-layer sort: group by layer, within each layer sort by diff desc ─
        candidates.sort(key=lambda x: (x[1], -x[0]))
        diff_lookup: dict = {}
        for diff_val, layer, feat_idx, *_ in candidates:
            key = (layer, feat_idx)
            if key not in diff_lookup or diff_val > diff_lookup[key]:
                diff_lookup[key] = diff_val
        tok_html, table_html = compare_to_html(candidates, text1, text2, tokens1_str, tokens2_str)
        return tok_html, table_html, diff_lookup

    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"Comparison failed: {e}")


# ─── CSS ─────────────────────────────────────────────────────────────────────

CSS = """
/* ══════════════════════════════════════════════════════════════════
   Color tokens — single source of truth for light / dark palettes
   ══════════════════════════════════════════════════════════════════ */
:root {
    --c-page-bg:      #f4f6fb;
    --c-card-bg:      #ffffff;
    --c-card-border:  #e4e7ef;
    --c-card-shadow:  0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    --c-header-bg:    linear-gradient(135deg,#eff6ff 0%,#e0eaff 55%,#ede9fe 100%);
    --c-header-border:#c7d2fe;
    --c-header-text:  #1e293b;
    --c-header-h1:    #1e3a8a;
    --c-header-p:     #475569;
    --c-pill-bg:      rgba(37,99,235,0.08);
    --c-pill-border:  rgba(37,99,235,0.22);
    --c-pill-text:    #1e3a8a;
    --c-chip-bg:      #eff4ff;
    --c-chip-text:    #2563eb;
    --c-btn2-bg:      #f8faff;
    --c-btn2-border:  #d0d7e8;
    --c-btn2-text:    #374151;
    --c-outbox-bg:    #fafbff;
    --c-outbox-text:  #1e293b;
    --c-outbox-border:#e4e7ef;
    --c-tab-text:     #374151;
    --c-tab-sel:      #2563eb;
    --c-divider:      #dde3f0;
    --c-th-bg:        #f0f4ff;
    --c-th-text:      #2563eb;
}

/* Dark mode via OS/browser preference */
@media (prefers-color-scheme: dark) {
    :root {
        --c-page-bg:      #0f172a;
        --c-card-bg:      #1e293b;
        --c-card-border:  #334155;
        --c-card-shadow:  0 1px 4px rgba(0,0,0,0.40), 0 4px 16px rgba(0,0,0,0.25);
        --c-header-bg:    linear-gradient(135deg,#172554 0%,#1e3a8a 55%,#3b0764 100%);
        --c-header-border:#1e40af;
        --c-header-text:  #e2e8f0;
        --c-header-h1:    #bfdbfe;
        --c-header-p:     #94a3b8;
        --c-pill-bg:      rgba(96,165,250,0.12);
        --c-pill-border:  rgba(96,165,250,0.30);
        --c-pill-text:    #93c5fd;
        --c-chip-bg:      #172554;
        --c-chip-text:    #93c5fd;
        --c-btn2-bg:      #1e293b;
        --c-btn2-border:  #475569;
        --c-btn2-text:    #e2e8f0;
        --c-outbox-bg:    #0f172a;
        --c-outbox-text:  #e2e8f0;
        --c-outbox-border:#334155;
        --c-tab-text:     #94a3b8;
        --c-tab-sel:      #60a5fa;
        --c-divider:      #334155;
        --c-th-bg:        #172554;
        --c-th-text:      #93c5fd;
    }
}

/* Dark mode via Gradio's explicit dark-mode class (toggled manually) */
.dark {
    --c-page-bg:      #0f172a;
    --c-card-bg:      #1e293b;
    --c-card-border:  #334155;
    --c-card-shadow:  0 1px 4px rgba(0,0,0,0.40), 0 4px 16px rgba(0,0,0,0.25);
    --c-header-bg:    linear-gradient(135deg,#172554 0%,#1e3a8a 55%,#3b0764 100%);
    --c-header-border:#1e40af;
    --c-header-text:  #e2e8f0;
    --c-header-h1:    #bfdbfe;
    --c-header-p:     #94a3b8;
    --c-pill-bg:      rgba(96,165,250,0.12);
    --c-pill-border:  rgba(96,165,250,0.30);
    --c-pill-text:    #93c5fd;
    --c-chip-bg:      #172554;
    --c-chip-text:    #93c5fd;
    --c-btn2-bg:      #1e293b;
    --c-btn2-border:  #475569;
    --c-btn2-text:    #e2e8f0;
    --c-outbox-bg:    #0f172a;
    --c-outbox-text:  #e2e8f0;
    --c-outbox-border:#334155;
    --c-tab-text:     #94a3b8;
    --c-tab-sel:      #60a5fa;
    --c-divider:      #334155;
    --c-th-bg:        #172554;
    --c-th-text:      #93c5fd;
}

/* ── Page background ── */
body, .gradio-container { background: var(--c-page-bg) !important; }

/* ── Header card ── */
.header-card {
    background: var(--c-header-bg);
    border-radius: 14px;
    padding: 22px 28px 18px;
    margin-bottom: 4px;
    color: var(--c-header-text);
    box-shadow: 0 4px 20px rgba(37,99,235,0.10);
    border: 1px solid var(--c-header-border);
}
.header-card h1 { margin:0 0 6px; font-size:24px; font-weight:700; letter-spacing:-.3px; color:var(--c-header-h1); }
.header-card p  { margin:0;       font-size:13px; color:var(--c-header-p); }
.stat-pill {
    display:inline-block;
    background:var(--c-pill-bg);
    border:1px solid var(--c-pill-border);
    border-radius:20px;
    padding:3px 13px;
    font-size:12px;
    color:var(--c-pill-text);
    margin:4px 3px 0;
}

/* ── Panel cards ── */
.panel-card {
    background: var(--c-card-bg) !important;
    border-radius: 12px !important;
    box-shadow: var(--c-card-shadow) !important;
    border: 1px solid var(--c-card-border) !important;
    padding: 18px !important;
}
.panel-card > .form { gap: 12px !important; }

/* ── Section label chips ── */
.section-chip {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: var(--c-chip-text);
    background: var(--c-chip-bg);
    border-radius: 6px;
    padding: 2px 10px;
    display: inline-block;
    margin-bottom: 10px;
}

/* ── Buttons ── */
.btn-primary {
    background: linear-gradient(135deg, #2563eb, #6d28d9) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: .2px !important;
    box-shadow: 0 2px 10px rgba(37,99,235,0.30) !important;
    transition: all 0.18s ease !important;
    color: #fff !important;
    padding: 10px 0 !important;
}
.btn-primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 18px rgba(37,99,235,0.40) !important;
}
.btn-secondary {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border: 1px solid var(--c-btn2-border) !important;
    background: var(--c-btn2-bg) !important;
    color: var(--c-btn2-text) !important;
    transition: all 0.15s ease !important;
}
.btn-secondary:hover {
    background: var(--c-chip-bg) !important;
    border-color: var(--c-tab-sel) !important;
}

/* ── Output boxes ── */
.output-box textarea {
    font-family: ui-monospace, monospace !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
    background: var(--c-outbox-bg) !important;
    color: var(--c-outbox-text) !important;
    border-color: var(--c-outbox-border) !important;
    border-radius: 8px !important;
}

/* ── Dataframe ── */
.feature-table table { font-family: ui-monospace, monospace; font-size: 13px; }
.feature-table th    { background: var(--c-th-bg) !important; color: var(--c-th-text) !important;
                        font-weight: 600; font-size: 12px; text-transform: uppercase; }

/* ── Tab styling ── */
.tab-nav button {
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 8px 8px 0 0 !important;
    color: var(--c-tab-text) !important;
}
.tab-nav button.selected {
    color: var(--c-tab-sel) !important;
    border-bottom: 2px solid var(--c-tab-sel) !important;
}

/* ── Divider ── */
.section-divider {
    border: none;
    border-top: 1px dashed var(--c-divider);
    margin: 6px 0 10px;
}

/* ── Slider label ── */
label.svelte-1b6s6sv { font-size: 13px !important; font-weight: 500 !important; }
"""

# ─── Build the Gradio interface ───────────────────────────────────────────────

with gr.Blocks(title="Qwen-Scope Feature Explorer") as demo:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.HTML(
        '<div class="header-card">'
        '  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
        '    <img src="https://cdn-avatars.huggingface.co/v1/production/uploads/620760a26e3b7210c2ff1943/-s1gyJfvbE1RgO5iBeNOi.png" alt="Qwen Logo" style="height:24px;width:auto;">'
        '    <h1 style="margin:0;">Qwen-Scope Feature Explorer</h1>'
        '  </div>'
        f'  <p>Interpret {MODEL_NAME_ANALYZING_NOW} via Sparse Autoencoders trained on each residual-stream layer from {MODEL_NAME_SAE_TRAINED_FROM}.</p>'
        '  <div style="margin-top:10px;">'
        f'    <span class="stat-pill">Model: {MODEL_NAME_ANALYZING_NOW}</span>'
        f'    <span class="stat-pill">SAE trained from: {MODEL_NAME_SAE_TRAINED_FROM}</span>'
        f'    <span class="stat-pill">Layers: {NUM_LAYERS}</span>'
        f'    <span class="stat-pill">SAE width: {SAE_WIDTH:,}</span>'
        f'    <span class="stat-pill">Top-k: {TOP_K}</span>'
        f'    <span class="stat-pill">d_model: {D_MODEL}</span>'
        '  </div>'
        '</div>'
    )

    analysis_state = gr.State(None)   # (list[str] tokens, Tensor[seq, sae_width] features)
    compare_diff_state = gr.State({})

    with gr.Tabs(elem_classes="tab-nav"):

        # ══════════════════════════════════════════════════════════════════════
        # Tab 1 — Feature Comparison
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("⚖️  Feature Comparison"):

            with gr.Row(equal_height=False):

                # ── Left column: inputs + settings + token preview ─────────────
                with gr.Column(scale=2, min_width=300):

                    with gr.Accordion("Examples", open=True) as t3_examples_accordion:
                        with gr.Group(elem_classes="panel-card"):
                            gr.HTML('<span class="section-chip">Examples</span>')
                            t3_text1 = gr.Textbox(
                                label="Example 1",
                                lines=5,
                                placeholder="Paste first text here…",
                            )
                            t3_text2 = gr.Textbox(
                                label="Example 2",
                                lines=5,
                                placeholder="Paste second text here…",
                            )

                    with gr.Accordion("Comparison Settings", open=True) as t3_settings_accordion:
                        with gr.Group(elem_classes="panel-card"):
                            gr.HTML('<span class="section-chip">Comparison Settings</span>')
                            with gr.Row():
                                t3_layer_from = gr.Slider(
                                    minimum=0, maximum=NUM_LAYERS - 1,
                                    value=0, step=1,
                                    label="Layer from",
                                    scale=1,
                                )
                                t3_layer_to = gr.Slider(
                                    minimum=0, maximum=NUM_LAYERS - 1,
                                    value=NUM_LAYERS - 1, step=1,
                                    label="Layer to",
                                    scale=1,
                                )
                            t3_topk = gr.Number(
                                value=5, precision=0,
                                label="Top-K results",
                                info="Number of (layer, feature) pairs to surface.",
                            )
                            with gr.Accordion("Advanced options", open=False):
                                t3_skip_first = gr.Checkbox(
                                    label="Exclude first token",
                                    value=False,
                                    info="Skip position 0 when computing mean activations.",
                                )
                                t3_remove_common_toks = gr.Checkbox(
                                    label="Remove common tokens",
                                    value=False,
                                    info="Exclude positions whose token ID appears in both examples.",
                                )
                                t3_remove_prefix = gr.Checkbox(
                                    label="Remove common prefix",
                                    value=False,
                                    info="Exclude the longest token-level prefix shared by both examples.",
                                )
                            t3_run = gr.Button(
                                "⚖️  Compare Features",
                                variant="primary",
                                elem_classes="btn-primary",
                            )

                    with gr.Accordion("Features", open=True) as t3_features_accordion:
                        with gr.Group(elem_classes="panel-card"):
                            gr.HTML(
                                '<span class="section-chip">Feature Comparison</span>'
                                '<span style="font-size:12px;color:#888;margin-left:8px;">'
                                'top-K features per layer · ranked by |rate(Ex1) − rate(Ex2)|'
                                ' where rate = fraction of token positions where the feature fires · grouped by layer'
                                '</span>'
                            )
                            t3_out = gr.HTML(
                                value=(
                                    '<div style="min-height:80px;display:flex;align-items:center;'
                                    'justify-content:center;color:#bbb;font-size:13px;">'
                                    'Enter two examples and click Compare.</div>'
                                )
                            )

                # ── Right column: token activations ───────────────────────────
                with gr.Column(scale=3, min_width=380):
                    with gr.Group(elem_classes="panel-card"):
                        gr.HTML(
                            '<span class="section-chip">Token Activations</span>'
                            '<span style="font-size:12px;color:#888;margin-left:8px;">'
                            'hover a feature row on the left to highlight activations'
                            '</span>'
                        )
                        t3_tok_html = gr.HTML(
                            value=(
                                '<div style="min-height:60px;display:flex;align-items:center;'
                                'justify-content:center;color:#bbb;font-size:13px;padding:8px;">'
                                'Run Compare to see token activations here.</div>'
                            )
                        )

        # ══════════════════════════════════════════════════════════════════════
        # Tab 2 — Feature Steering
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("🎛️  Feature Steering"):

            with gr.Row(equal_height=False):

                # ── Left column: prompt + steering controls ────────────────
                with gr.Column(scale=2, min_width=280):
                    with gr.Group(elem_classes="panel-card"):
                        gr.HTML('<span class="section-chip">Prompt</span>')
                        t2_prompt = gr.Textbox(
                            label=None,
                            lines=5,
                            placeholder="Enter a generation prompt…",
                            show_label=False,
                        )

                        t2_apply_think = gr.Checkbox(
                            label="Apply default thinking template",
                            value=False,
                            info=(
                                "Wrap the prompt in the ChatML format with thinking enabled "
                                "(assistant prefill starts with <think>)."
                            ),
                        )
                        t2_apply_nothink = gr.Checkbox(
                            label="Apply default no-thinking template",
                            value=False,
                            info=(
                                "Wrap the prompt in the ChatML format with thinking disabled "
                                "(assistant prefill starts with <think>\\n\\n</think>)."
                            ),
                        )
                        t2_template_info = gr.HTML(visible=False, value="")

                        gr.HTML('<span class="section-chip">Token Position Preview</span>'
                                '<span style="font-size:12px;color:#888;margin-left:8px;">'
                                'amber = steered &nbsp;·&nbsp; updates as you type'
                                '</span>')

                        t2_pos_preview = gr.HTML(
                            value=(
                                '<div style="padding:10px;color:#bbb;font-size:13px;">'
                                'Enter a prompt above to preview steered positions.</div>'
                            )
                        )

                    with gr.Group(elem_classes="panel-card"):
                        gr.HTML('<span class="section-chip">Steering Parameters</span>')

                        with gr.Row():
                            t2_layer = gr.Slider(
                                minimum=0, maximum=NUM_LAYERS - 1,
                                value=10, step=1,
                                label="Layer",
                                scale=3,
                            )
                            t2_feat = gr.Number(
                                value=0, precision=0,
                                label="Feature index",
                                info=f"0 – {SAE_WIDTH - 1}",
                                scale=2,
                            )

                        t2_pos = gr.Textbox(
                            label="Token positions to steer",
                            value="all",
                            placeholder="all  |  0,1,5  |  3-7  |  0,2,5-8",
                            info=(
                                "all → every token  |  "
                                "0,1,5 → individual positions  |  "
                                "3-7 → inclusive range  |  "
                                "combinations e.g. 0,2,5-8"
                            ),
                        )
                        t2_steer_output_only = gr.Checkbox(
                            label="Also steer generated tokens",
                            value=True,
                            info=(
                                "When enabled, every generated token is steered in addition to "
                                "whatever the positions field specifies for the prompt."
                            ),
                        )

                        gr.HTML('<span class="section-chip">Steering Strength</span>')
                        t2_steer_mode = gr.Radio(
                            choices=["Light", "Medium", "Strong", "Custom"],
                            value="Light",
                            label=None,
                            show_label=False,
                            info=(
                                "Calibrated to the most different feature found in "
                                "Feature Comparison. Run that tab first."
                            ),
                        )
                        t2_custom_strength = gr.Number(
                            value=5.0,
                            label="Custom strength",
                            info="Direct steering magnitude (used when Custom is selected above).",
                            visible=False,
                            precision=2,
                        )
                        t2_steer_info = gr.HTML(
                            value=(
                                '<div style="font-size:11px;color:#888;padding:4px 6px;'
                                'background:#f8faff;border-radius:5px;">'
                                'Light ≈ 5.0 · Medium ≈ 20.0 · Strong ≈ 100.0<br>'
                                '<span style="color:#bbb;">Run Feature Comparison to calibrate.</span>'
                                '</div>'
                            )
                        )

                        gr.HTML('<hr class="section-divider">')
                        with gr.Accordion("Sampling options", open=False):
                            t2_maxtok = gr.Slider(
                                minimum=20, maximum=300,
                                value=100, step=10,
                                label="Max new tokens",
                            )
                            t2_greedy = gr.Checkbox(
                                label="Greedy decoding",
                                value=True,
                                info="When enabled, all sampling parameters below are ignored.",
                            )
                            with gr.Row():
                                t2_temperature = gr.Slider(
                                    minimum=0.01, maximum=2.0,
                                    value=GEN_TEMPERATURE, step=0.01,
                                    label="Temperature",
                                    interactive=GEN_DO_SAMPLE,
                                )
                                t2_top_p = gr.Slider(
                                    minimum=0.0, maximum=1.0,
                                    value=GEN_TOP_P, step=0.01,
                                    label="Top-p (nucleus)",
                                    interactive=GEN_DO_SAMPLE,
                                )
                            with gr.Row():
                                t2_top_k_tok = gr.Slider(
                                    minimum=0, maximum=200,
                                    value=GEN_TOP_K, step=1,
                                    label="Top-k (tokens)",
                                    info="0 = disabled",
                                    interactive=GEN_DO_SAMPLE,
                                )
                                t2_rep_penalty = gr.Slider(
                                    minimum=1.0, maximum=3.0,
                                    value=GEN_REP_PENALTY, step=0.05,
                                    label="Repetition penalty",
                                    info="1.0 = no penalty",
                                    interactive=GEN_DO_SAMPLE,
                                )

                        t2_run = gr.Button(
                            "▶  Generate Both Outputs",
                            variant="primary",
                            elem_classes="btn-primary",
                        )

                # ── Right column: outputs ──────────────────────────────────
                with gr.Column(scale=3, min_width=380):

                    with gr.Group(elem_classes="panel-card"):
                        gr.HTML(
                            '<span class="section-chip">Original Output</span>'
                            '<span style="font-size:12px;color:#888;margin-left:8px;">'
                            'No steering applied</span>'
                        )
                        t2_orig = gr.Textbox(
                            label=None, lines=7,
                            interactive=False,
                            show_label=False,
                            placeholder="Original generation will appear here…",
                            elem_classes="output-box",
                        )
                        gr.HTML(
                            '<span class="section-chip" style="margin-top:10px;'
                            'display:inline-block;">Token Probabilities</span>'
                            '<span style="font-size:12px;color:#888;margin-left:8px;">'
                            'blue intensity = confidence &nbsp;·&nbsp; hover = top-k</span>'
                        )
                        t2_orig_probs = gr.HTML(
                            value='<div style="padding:10px;color:#bbb;font-size:13px;">'
                                  'Run generation to see token probabilities.</div>'
                        )

                    with gr.Group(elem_classes="panel-card"):
                        gr.HTML(
                            '<span class="section-chip" style="background:#fef3f2;color:#dc2626;">'
                            'Steered Output</span>'
                            '<span style="font-size:12px;color:#888;margin-left:8px;">'
                            'With SAE feature injection</span>'
                        )
                        t2_steered = gr.Textbox(
                            label=None, lines=7,
                            interactive=False,
                            show_label=False,
                            placeholder="Steered generation will appear here…",
                            elem_classes="output-box",
                        )
                        gr.HTML(
                            '<span class="section-chip" style="background:#fef3f2;color:#dc2626;'
                            'margin-top:10px;display:inline-block;">Token Probabilities</span>'
                            '<span style="font-size:12px;color:#888;margin-left:8px;">'
                            'red intensity = confidence &nbsp;·&nbsp; hover = top-k</span>'
                        )
                        t2_steer_probs = gr.HTML(
                            value='<div style="padding:10px;color:#bbb;font-size:13px;">'
                                  'Run generation to see token probabilities.</div>'
                        )

            t2_run.click(
                cb_generate,
                inputs=[t2_prompt, t2_layer, t2_feat, t2_pos, t2_steer_mode, compare_diff_state,
                        t2_steer_output_only, t2_maxtok,
                        t2_greedy, t2_top_k_tok, t2_top_p, t2_rep_penalty,
                        t2_temperature, t2_custom_strength, t2_apply_think, t2_apply_nothink],
                outputs=[t2_orig, t2_steered, t2_orig_probs, t2_steer_probs],
            )
            t3_run.click(
                cb_compare,
                inputs=[t3_text1, t3_text2, t3_layer_from, t3_layer_to, t3_topk,
                        t3_skip_first, t3_remove_common_toks, t3_remove_prefix],
                outputs=[t3_tok_html, t3_out, compare_diff_state],
            ).then(
                fn=lambda: [gr.update(open=False), gr.update(open=False)],
                inputs=None,
                outputs=[t3_examples_accordion, t3_settings_accordion],
            )
            _sampling_controls = [
                t2_temperature, t2_top_p, t2_top_k_tok, t2_rep_penalty
            ]
            t2_greedy.change(
                fn=lambda g: [gr.update(interactive=not g)] * 4,
                inputs=[t2_greedy],
                outputs=_sampling_controls,
            )
            t2_prompt.change(
                cb_update_steer_preview,
                inputs=[t2_prompt, t2_pos, t2_apply_think, t2_apply_nothink],
                outputs=[t2_pos_preview],
            )
            t2_pos.change(
                cb_update_steer_preview,
                inputs=[t2_prompt, t2_pos, t2_apply_think, t2_apply_nothink],
                outputs=[t2_pos_preview],
            )

            def _update_steer_info(mode: str, diff_lookup, layer, feat_idx):
                if mode == "Custom":
                    return (
                        '<div style="font-size:11px;color:#555;padding:4px 6px;'
                        'background:#f8faff;border-radius:5px;">'
                        'Enter a custom steering strength value above.'
                        '</div>'
                    )
                d = 0.0
                source_note = '<span style="color:#bbb;">Run Feature Comparison to calibrate.</span>'
                if diff_lookup and isinstance(diff_lookup, dict):
                    key = (int(layer), int(feat_idx))
                    if key in diff_lookup:
                        d = float(diff_lookup[key])
                        source_note = (
                            f'<span style="color:#16a34a;">feature #{int(feat_idx)} '
                            f'@ layer {int(layer)} · diff = {d:.3f}</span>'
                        )
                    else:
                        d = float(max(diff_lookup.values(), default=0.0))
                        source_note = (
                            f'<span style="color:#64748b;">feature not in compare results — '
                            f'using global max diff = {d:.3f}</span>'
                        )
                if d <= 0:
                    vals = {"Light": 5.0, "Medium": 20.0, "Strong": 100.0}
                else:
                    vals = {
                        "Light":  round(d * 0.5, 2),
                        "Medium": round(d * 2.0, 2),
                        "Strong": round(d * 10.0, 2),
                    }
                return (
                    f'<div style="font-size:11px;color:#555;padding:4px 6px;'
                    f'background:#f8faff;border-radius:5px;">'
                    f'Light ≈ {vals["Light"]} · Medium ≈ {vals["Medium"]} · Strong ≈ {vals["Strong"]}<br>'
                    + source_note + '</div>'
                )

            _steer_info_inputs = [t2_steer_mode, compare_diff_state, t2_layer, t2_feat]
            for _trigger in [t2_steer_mode.change, compare_diff_state.change,
                             t2_layer.change, t2_feat.change]:
                _trigger(
                    fn=_update_steer_info,
                    inputs=_steer_info_inputs,
                    outputs=[t2_steer_info],
                )

            # Show/hide custom strength input depending on radio selection
            t2_steer_mode.change(
                fn=lambda m: gr.update(visible=(m == "Custom")),
                inputs=[t2_steer_mode],
                outputs=[t2_custom_strength],
            )

            # ── Template toggle: mutual exclusion + info panel + preview refresh ─
            _THINK_INFO_HTML = (
                '<div style="font-size:11px;color:#555;padding:6px 10px;'
                'background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;'
                'font-family:ui-monospace,monospace;white-space:pre-wrap;line-height:1.7;">'
                '&lt;|im_start|&gt;user\n'
                '&#123;your prompt&#125;&lt;|im_end|&gt;\n'
                '&lt;|im_start|&gt;assistant\n'
                '&lt;think&gt;\n'
                '</div>'
            )
            _NOTHINK_INFO_HTML = (
                '<div style="font-size:11px;color:#555;padding:6px 10px;'
                'background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;'
                'font-family:ui-monospace,monospace;white-space:pre-wrap;line-height:1.7;">'
                '&lt;|im_start|&gt;user\n'
                '&#123;your prompt&#125;&lt;|im_end|&gt;\n'
                '&lt;|im_start|&gt;assistant\n'
                '&lt;think&gt;\n\n&lt;/think&gt;\n\n'
                '</div>'
            )

            def _on_think_change(think_val, nothink_val, prompt, pos_str):
                if think_val:
                    # Just checked: uncheck nothink, show think format, refresh preview
                    return (gr.update(value=False),
                            gr.update(visible=True, value=_THINK_INFO_HTML),
                            cb_update_steer_preview(prompt, pos_str, True, False))
                elif nothink_val:
                    # Unchecked by mutual exclusion — nothink is active; leave info+preview alone
                    return gr.update(), gr.update(), gr.update()
                else:
                    # Manually unchecked with nothing active — reset to raw
                    return (gr.update(),
                            gr.update(visible=False),
                            cb_update_steer_preview(prompt, pos_str, False, False))

            def _on_nothink_change(nothink_val, think_val, prompt, pos_str):
                if nothink_val:
                    # Just checked: uncheck think, show nothink format, refresh preview
                    return (gr.update(value=False),
                            gr.update(visible=True, value=_NOTHINK_INFO_HTML),
                            cb_update_steer_preview(prompt, pos_str, False, True))
                elif think_val:
                    # Unchecked by mutual exclusion — think is active; leave info+preview alone
                    return gr.update(), gr.update(), gr.update()
                else:
                    # Manually unchecked with nothing active — reset to raw
                    return (gr.update(),
                            gr.update(visible=False),
                            cb_update_steer_preview(prompt, pos_str, False, False))

            t2_apply_think.change(
                fn=_on_think_change,
                inputs=[t2_apply_think, t2_apply_nothink, t2_prompt, t2_pos],
                outputs=[t2_apply_nothink, t2_template_info, t2_pos_preview],
            )
            t2_apply_nothink.change(
                fn=_on_nothink_change,
                inputs=[t2_apply_nothink, t2_apply_think, t2_prompt, t2_pos],
                outputs=[t2_apply_think, t2_template_info, t2_pos_preview],
            )


# Pre-load model onto GPU before accepting requests, so the first
# button click doesn't stall waiting for a 30 B-param model to load.
print("Pre-loading model onto GPU…")
get_model()
print("Model ready. Starting Gradio server…")
demo.queue(max_size=4)
demo.launch(
    server_name="0.0.0.0",
    server_port=PORT,
    # share=True creates a public gradio.live URL that bypasses the
    # Alibaba Cloud DSW gateway (which blocks POST API requests).
    # The URL printed below is valid for 72 h.
    share=True,
    strict_cors=False,
    show_error=True,
    ssr_mode=False,
    theme=gr.themes.Soft(),
    css=CSS,
)
