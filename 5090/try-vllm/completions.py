from vllm import LLM

#  https://docs.vllm.ai/en/stable/api/offline_inference/llm.html
llm = LLM(model="Qwen/Qwen2.5-7B-Instruct")
response = llm.generate("hello, who are you?")
first = response[0]
print(f"prompt: {first.prompt}")
first_output = first.outputs[0]
print(f"first output:")
print(f"  text: {first_output.text}")
print(f"  finished: {first_output.finished()}")
print(f"    finish reason: {first_output.finish_reason}")


