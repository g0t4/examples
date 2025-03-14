from vllm import LLM
import time


class Timer:

    def __init__(self, message=""):
        self.message = message

    def __enter__(self):
        self.start_ns = time.time_ns()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_ns = time.time_ns()
        elapsed_ns = self.end_ns - self.start_ns
        elapsed_ms = elapsed_ns / 1000000
        print(f"wall time ({self.message}): {elapsed_ms:.2f} ms")


llm = LLM(model="Qwen/Qwen2.5-0.5B-Instruct")
# TODO prod it for longer response?

with Timer("llm.generate"):
    # TODO capture generate_wall_time_ms and use it to compute tokens per walltimesecond
    outputs = llm.generate(["Hello, world!"])

print("\n\n") # leave blank lines b/c of all module load output
if len(outputs) != 1:
    print("Expected 1 output, so timing is not correct below")

response = outputs[0]
assert response is not None
metrics = response.metrics
assert metrics is not None
assert metrics.first_token_time is not None
assert metrics.last_token_time is not None

duration_seconds = (metrics.last_token_time - metrics.first_token_time)
duration_ms = duration_seconds * 1000
# PRN scheduler_time=0.0008704509818926454 ... is this useful to know?
if len(response.outputs) != 1:
    print("Expected 1 nested output, so timing is not correct below")

completion = response.outputs[0]
print(f"text: {completion.text}")
num_tokens = len(completion.token_ids)
print(f"  num_tokens: {num_tokens}")
if response.num_cached_tokens is not None:
    print(f"  num_cached_tokens: {response.num_cached_tokens}")
tokens_per_second = num_tokens / duration_seconds
print(f"  duration_ms: {duration_ms:.2f} ms")
print(f"  tokens per second: {tokens_per_second:.2f}")
print(f"  ms per token: {duration_ms / num_tokens:.2f}")

# TODO find a way to compare end to end timing vs HTTP API, for an example that is dominated by generation time (1000s of tokens)
