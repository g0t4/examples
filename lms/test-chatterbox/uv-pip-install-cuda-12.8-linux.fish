#!/usr/bin/env fish

rm -rf .venv
uv venv


# install cuda 12.8 stable.. v2.7.0 currently pytorch
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128


uv pip install chatterbox-tts --no-deps
# NEXT TIME just have grok build full list for you, after your initial torch install
# then basically I did
#  uv pip install --dry-run chatterbox-tts  
#     then review what is missing while doing
#     uv run main.py  # test each time if I have enough to get sampling passing

#  first handful I tried install => run => install => run ... to find whats missing
#    technically I should've installed the version listed in dry run but I didn't...next time do that
uv pip install --no-deps librosa lazy-loader resemble-perth \
    huggingface-hub requests urllib3 idna certifi tqdm \
    audioread cffi cfgv charset-normalizer \
    conformer decorator zipp

# this one needs the specific version b/c otherwise the some data format is v3 vs v4 and yeah... just use explicit version
uv pip install --no-deps antlr4-python3-runtime==4.9.3

# ok so now I got tired of one by one... asked Grok to build me a pip install based on output of --dry-run
# this is what he gave me (checked too and he did good except he missed the last one zipp.. which I then moved above)
uv pip install --no-deps \
    diffusers==0.29.0 \
    distlib==0.3.9 \
    einops==0.8.1 \
    hf-xet==1.1.2 \
    identify==2.6.12 \
    importlib-metadata==8.7.0 \
    joblib==1.5.1 \
    llvmlite==0.44.0 \
    msgpack==1.1.0 \
    nodeenv==1.9.1 \
    numba==0.61.0 \
    omegaconf==2.3.0 \
    onnx==1.18.0 \
    packaging==25.0 \
    platformdirs==4.3.8 \
    pooch==1.8.2 \
    pre-commit==4.2.0 \
    protobuf==6.31.1 \
    pycparser==2.22 \
    pyyaml==6.0.2 \
    regex==2024.11.6 \
    resampy==0.4.3 \
    s3tokenizer==0.1.7 \
    safetensors==0.5.3 \
    scikit-learn==1.6.1 \
    scipy==1.15.3 \
    soundfile==0.13.1 \
    soxr==0.5.0.post1 \
    threadpoolctl==3.6.0 \
    tokenizers==0.20.3 \
    transformers==4.46.3 \
    virtualenv==20.31.2
