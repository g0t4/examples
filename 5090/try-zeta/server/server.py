import asyncio
import httpx
from flask import Flask, request, jsonify
import os
import time
from rich import print as rich_print

print = rich_print

# based on:
# https://github.com/zed-industries/zed/blob/35fbe1ef3d/crates/collab/src/llm.rs#L439
#    RIGHT BEFORE THEY REMOVED THIS IN PR 23997
#
# also reverse engineered from dataset repo on huggingface... (see other files in this try-zeta dir)
#    https://huggingface.co/datasets/zed-industries/zeta
#    btw I don't see outline in  SFT/DPO ipynb (notebooks) in hf dataset repo!? are those old?
#      or did they just add outline and it happens to not cause trouble? and be helpful without any SFT?
#      or is there a newer model :) and train dataset :)
#
# FYI to test this
#   export ZED_PREDICT_EDITS_URL=http://build21:PORT/predict_edits # or w/e route I use below
#   zed  # zed will use the URL for request (already confirmed this works)

#
# TODO try run quantized and/or ngram spec dec too:
#  vllm serve zed-industries/zeta --served-model-name zeta --enable-prefix-caching --enable-chunked-prefill --quantization="fp8" --speculative-model [ngram] --ngram-prompt-lookup-max 4 --ngram-prompt-lookup-min 2 --num-speculative-tokens 8
#  FYI this is mentioned in model card... IIAC this is how they're serving the actual zeta model (or at the time)
#    https://huggingface.co/zed-industries/zeta
#    do some speed tests w/ and w/o spec dec
#
#  TODO review below and touch up to work with the released HF zeta model

# FYI from zeta cask
# const CURSOR_MARKER: &'static str = "<|user_cursor_is_here|>";
# const START_OF_FILE_MARKER: &'static str = "<|start_of_file|>";
# const EDITABLE_REGION_START_MARKER: &'static str = "<|editable_region_start|>";
# const EDITABLE_REGION_END_MARKER: &'static str = "<|editable_region_end|>";
# const BUFFER_CHANGE_GROUPING_INTERVAL: Duration = Duration::from_secs(1);
# const ZED_PREDICT_DATA_COLLECTION_CHOICE: &str = "zed_predict_data_collection_choice";

app = Flask(__name__)

# PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")
PREDICTION_API_URL = "http://localhost:8000/v1/completions"


@app.route('/predict_edits', methods=['POST'])
def predict_edits():
    data = request.get_json()
    print("## headers", request.headers)
    print("## data", data)
    outline = data.get('outline', '')  # TODO validate input_outline (is name zed sends)
    input_events = data.get('input_events', '')  # TODO validate input_events (from zed)
    input_excerpt = data.get('input_excerpt', '')  # TODO validate input_excerpt (from zed)
    # TODO more params
    # speculated_output: Some(values.speculated_output), # TODO what is this for? seems to be a subset of input_excerpt?
    # can_collect_data,
    # diagnostic_groups # TODO capture example of this

    # TODO is this the right outline prefix/header?
    outline_prefix = f"### Outline for current file:\n{outline}\n" if outline else ""
    if outline:
        # TODO outline
        print("[WARN]: outline not yet supported")

    # TODO is there a header before Instruction?
    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(input_events, input_excerpt)
    print("## prompt:", prompt)

    # TODO pass outline
    # TODO any thing else passed in current version?
    # zeta client request body builder:
    #   https://github.com/zed-industries/zed/blob/17ecf94f6f/crates/zeta/src/zeta.rs#L449-L466
    # TODO capture request AND response
    #   TODO validate response format! from API
    async def fetch_prediction():
        timeout_sec = 30  # TODO timeout?
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            response = await client.post(
                PREDICTION_API_URL,
                # headers={"Authorization": f"Bearer {PREDICTION_API_KEY}"},
                json={
                    # "model": "zeta", -- do not need with vllm backend
                    "prompt": prompt,
                    "max_tokens": 2048,  # PR 23997 used 2048 # TODO what max? # can I get it to just stop on EOT?
                    # TODO should I set EOT to be the end of the template token(s)?
                    #
                    "temperature": 0.0,  # 23997 PR used 0 # TODO what value to use?
                    # "top_p": 0.9, # TODO value?
                    # "n": 1, # s/b default
                    # "stop": null # TODO what value?
                    # "rewrite_speculation": True # TODO?
                })
            result = response.json()
            print("\n\n## result", result)
            response.raise_for_status()
            choice_text = result.get("choices", [{}])[0].get("text", "")

            response_id = result["id"].replace("cmpl-","")

            return {
                #     pub output_excerpt: String,
                "output_excerpt": choice_text,
                #
                # FYI PR/23997 does not set request_id so lets skip for now, was only in zeta codebase
                #     pub request_id: Uuid,
                "request_id": response_id,  # FYI zed log shows "missing field `request_id`" error message
                # here is where crates/zeta uses reuest_id:
                #   https://github.com/zed-industries/zed/blob/17ecf94f6f/crates/zeta/src/zeta.rs#L845
                #   not sure this is then used anywhere
            }

    try:
        output = asyncio.run(fetch_prediction())
        print("\n\n## output", output)
        return jsonify(output)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=9000, host="0.0.0.0")
