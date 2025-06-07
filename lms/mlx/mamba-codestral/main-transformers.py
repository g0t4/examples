from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("mlx-community/Mamba-Codestral-7B-v0.1")
model = AutoModelForCausalLM.from_pretrained(
    "mlx-community/Mamba-Codestral-7B-v0.1",
    torch_dtype="auto",
    device_map="auto"
)

inputs = tokenizer("def hello_world():", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))
