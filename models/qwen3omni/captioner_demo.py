import soundfile as sf

from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info
from transformers import BitsAndBytesConfig

# %% 

MODEL_PATH = "Qwen/Qwen3-Omni-30B-A3B-Captioner"
from transformers import Qwen3OmniMoeConfig

config = Qwen3OmniMoeConfig.from_pretrained(MODEL_PATH)

if not hasattr(config, "initializer_range"):
    config.initializer_range = 0.02  # standard default

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,   # or load_in_8bit=True
    bnb_4bit_compute_dtype="bfloat16",
)

model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    dtype="auto",
    config=config,
    device_map="cuda",
    trust_remote_code=True,
    # torch_dtype="bfloat16",  # or float16
    # attn_implementation="sdpa",
    attn_implementation="flash_attention_2",
    quantization_config=bnb_config,
)

# %% 

processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_PATH)

# hack to get to work on cm 12.0... transformers complains about need cm 9.0... gah ... make it look like _grouped_mm is not supported
# PRN find a way to make it work w/ _grouped_mm?
import torch
if hasattr(torch, "_grouped_mm"):
    del torch._grouped_mm

# %% 

def react_to(audio_file, instructions):
    content = [ {"type": "audio", "audio": audio_file} ]
    if instructions:
        content += [{ "type": "text", "text": instructions} ]

    conversation = [
        {
            "role": "user",
            "content": content,
        },
    ]
    print(conversation)

    # Preparation for inference
    text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
    audios, _, _ = process_mm_info(conversation, use_audio_in_video=False)

    inputs = processor(text=text, 
                       audio=audios,
                       return_tensors="pt", 
                       padding=True, 
                       use_audio_in_video=False)
    inputs = inputs.to(model.device).to(model.dtype)

    # Inference: Generation of the output text (apparently can do audio too but not in above example)
    text_ids = model.generate(**inputs, thinker_return_dict_in_generate=True)

    text = processor.batch_decode(text_ids.sequences[:, inputs["input_ids"].shape[1] :],
                                  skip_special_tokens=True,
                                  clean_up_tokenization_spaces=False)
    print(text)

# {"type": "audio", "audio": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/caption2.mp3"},
# { "type": "text", "text": "Briefly describe this audio, from a screencast recording. I need to know if this is breathing or not." },
# {"type": "audio", "audio": audio_file},
# { "type": "text", "text": 
# react_to("clip40.wav", None)
react_to("clip40.wav", "ONLY respond with transcription, nothing else")

# %% 

classify = """This is a clip from a screencast. 
You are helping me produce splits for video editing between demo segments, retakes, etc.
I use algorithms to split up segments and then I need your help to double check the audio between segments.
Please classify this clip as: speaking, keystroke(s), breathing, no sounds"""
# FYI with better instructions, Qwen does better identifying breathing in clip10 (clip11 it always gets right as breathing)
# clip30.wav => no sounds at all...
#   if I provide "silence" as a category, qwen3omni is not classifying it as "silence"
#   but when I provide "no sounds" then it does classify it correctly!
#   
react_to("clip10.wav", classify)
react_to("clip11.wav", classify)
react_to("clip20.wav", classify)
react_to("clip30.wav", classify)
react_to("clip40.wav", classify)
