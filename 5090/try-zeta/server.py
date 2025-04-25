import asyncio
import httpx
from flask import Flask, request, jsonify
import os
import time

# based on:
# https://github.com/zed-industries/zed/blob/35fbe1ef3d/crates/collab/src/llm.rs#L439
# and also reverse engineered from dataset repo on huggingface... (see other files in this try-zeta dir)
#   https://huggingface.co/datasets/zed-industries/zeta
#   btw I don't see outline in  SFT/DPO ipynb (notebooks) in hf dataset repo!? are those old?
#     or did they just add outline and it happens to not cause trouble? and be helpful without any SFT? 
#     or is there a newer model :) and train dataset :)
#
# FYI to test this
#   export ZED_PREDICT_EDITS_URL=http://build21:PORT/predict_edits/v2 # or w/e route I use below
#   zed  # zed will use the URL for request (already confirmed this works)
#
# TODO try run quantized and/or ngram spec dec too:
#  vllm serve zed-industries/zeta --served-model-name zeta --enable-prefix-caching --enable-chunked-prefill --quantization="fp8" --speculative-model [ngram] --ngram-prompt-lookup-max 4 --ngram-prompt-lookup-min 2 --num-speculative-tokens 8
#  FYI this is mentioned in model card... IIAC this is how they're serving the actual zeta model (or at the time)
#    https://huggingface.co/zed-industries/zeta
#    do some speed tests w/ and w/o spec dec
#
#  TODO review below and touch up to work with the released HF zeta model


app = Flask(__name__)

PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")
PREDICTION_API_KEY = os.getenv("PREDICTION_API_KEY")
PREDICTION_MODEL = os.getenv("PREDICTION_MODEL", "default-model")
MAX_OUTPUT_TOKENS = 512

@app.route('/predict_edits/v2', methods=['POST'])
def predict_edits():
    data = request.get_json()
    outline = data.get('outline', '')
    input_events = data.get('input_events', '')
    input_excerpt = data.get('input_excerpt', '')
    can_collect_data = data.get('can_collect_data', False)

    outline_prefix = f"### Outline for current file:\n{outline}\n" if outline else ""
    
    # Mocked prediction prompt template
    prompt_template = """<outline><events><excerpt>"""
    prompt = prompt_template.replace("<outline>", outline_prefix)\
                             .replace("<events>", input_events)\
                             .replace("<excerpt>", input_excerpt)

    async def fetch_prediction():
        timeout_sec = 2
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            response = await client.post(
                PREDICTION_API_URL,
                headers={"Authorization": f"Bearer {PREDICTION_API_KEY}"},
                json={
                    "model": PREDICTION_MODEL,
                    "prompt": prompt,
                    "max_tokens": MAX_OUTPUT_TOKENS,
                    "temperature": 0.0,
                    "prediction": {"content": input_excerpt},
                    "rewrite_speculation": True
                }
            )
            response.raise_for_status()
            result = response.json()
            choice_text = result.get("choices", [{}])[0].get("text", "")
            return {"output_excerpt": choice_text}

    start_time = time.time()
    try:
        output = asyncio.run(fetch_prediction())
        duration = time.time() - start_time
        # Simulate sampling/logging if needed
        return jsonify(output)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000)

