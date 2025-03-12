from vllm import LLM

#  https://docs.vllm.ai/en/stable/api/offline_inference/llm.html
llm = LLM(model="Qwen/Qwen2.5-7B-Instruct")
llm.get_default_sampling_params()

tokenizer = llm.get_tokenizer()
print("vocab siz: ", len(tokenizer.get_vocab()))

# IIUC these are for lookup acros models?
print("tokenizer.SPECIAL_TOKENS_ATTRIBUTES: ", tokenizer.SPECIAL_TOKENS_ATTRIBUTES)

# chat template
chat_template = tokenizer.get_chat_template()
print("chat template: ", chat_template)

# tokenize:
tokenizer("foo the bar")
# {'input_ids': [7975, 279, 3619], 'attention_mask': [1, 1, 1]}

# HERE WE GO (actual instance)
engine = llm.llm_engine
# found this:
#   https://github.com/g0t4/examples/blob/master/5090/try-vllm/.venv/lib/python3.12/site-packages/vllm/entrypoints/llm.py#L242
# BTW llm.get_engine_class() returns a type, not instance
model_config = engine.model_config
print(f"architectures: {model_config.architectures}") # ['Qwen2ForCausalLM']
print(f"dtype: {model_config.dtype}") # torch.bfloat16

print(f"hf_config: {model_config.hf_config}")
# hf_config: Qwen2Config {
#   "_name_or_path": "Qwen/Qwen2.5-7B-Instruct",
#   "architectures": [
#     "Qwen2ForCausalLM"
#   ],
#   "attention_dropout": 0.0,
#   "bos_token_id": 151643,
#   "eos_token_id": 151645,
#   "hidden_act": "silu",
#   "hidden_size": 3584,
#   "initializer_range": 0.02,
#   "intermediate_size": 18944,
#   "max_position_embeddings": 32768,
#   "max_window_layers": 28,
#   "model_type": "qwen2",
#   "num_attention_heads": 28,
#   "num_hidden_layers": 28,
#   "num_key_value_heads": 4,
#   "rms_norm_eps": 1e-06,
#   "rope_scaling": null,
#   "rope_theta": 1000000.0,
#   "sliding_window": 131072,
#   "tie_word_embeddings": false,
#   "torch_dtype": "bfloat16",
#   "transformers_version": "4.49.0",
#   "use_cache": true,
#   "use_sliding_window": false,
#   "vocab_size": 152064
# }
