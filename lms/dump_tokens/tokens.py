import re
from transformers import AutoTokenizer

# Load tokenizer (adjust model path if needed)
# tokenizer = AutoTokenizer.from_pretrained("openai/gpt-oss-20b")
tokenizer = AutoTokenizer.from_pretrained("ByteDance-Seed/Seed-Coder-8B-Base") # https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Base/blob/main/tokenizer_config.json 
# tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B")

print(f"{tokenizer.vocab_size=}")
print(f"{len(tokenizer)=}")

real_vocab_size = max(tokenizer.vocab_size, len(tokenizer))
print(f"{real_vocab_size=}")

print(tokenizer.special_tokens_map)
print(tokenizer.additional_special_tokens)

def search_for(search_regex):
    for num in range(real_vocab_size):
        token = tokenizer.convert_ids_to_tokens(num)
        if re.search(search_regex, token, re.IGNORECASE):
            print(token)

search_for(r'fim')
search_for(r'suffix')
search_for(r'prefix')
search_for(r'middle')

# print last X tokens from end of list (past vocab_size)
for i in range(tokenizer.vocab_size, real_vocab_size): 
    print(f"{i}: " + tokenizer.convert_ids_to_tokens(i))

# look_for_tokens = ["<|fim_prefix|>", "<|fim_middle|>", "<|fim_suffix|>"] # gptoss
look_for_tokens = ["<[fim-prefix]>", "<[fim-middle]>", "<[fim-suffix]>"] # ByteDance Seed-Coder 
look_for_ids = tokenizer.convert_tokens_to_ids(look_for_tokens)
print(look_for_ids)  
print(tokenizer.convert_ids_to_tokens(look_for_ids))



print()
print("----")
for i in range(0, 500):
    print(f"{i}: " + tokenizer.convert_ids_to_tokens(i))

