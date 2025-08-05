import re
from transformers import AutoTokenizer

# Load tokenizer (adjust model path if needed)
# tokenizer = AutoTokenizer.from_pretrained("openai/gpt-oss-20b")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B")

print(f"{tokenizer.vocab_size=}")
print(f"{len(tokenizer)=}")

real_vocab_size = max(tokenizer.vocab_size, len(tokenizer))
print(f"{real_vocab_size=}")

print(tokenizer.special_tokens_map)
print(tokenizer.additional_special_tokens)

for num in range(real_vocab_size):
    token = tokenizer.convert_ids_to_tokens(num)
    if re.search(r'fim', token, re.IGNORECASE):
        print(token)

look_for_tokens = ["<|fim_prefix|>", "<|fim_middle|>", "<|fim_suffix|>"]
look_for_ids = tokenizer.convert_tokens_to_ids(look_for_tokens)
print(look_for_ids)  
print(tokenizer.convert_ids_to_tokens(look_for_ids))
