import requests
import json

num_ctx = 48128 # half of char count is plenty
model = "llama3.1:8b"

# num_ctx = 32768
# model = "mistral"

#num_ctx = 163840
#model = "deepseek-coder-v2:latest"

# use_file="bypass.html"
use_file="drop-svgs.html"
with open(use_file, "r") as f:
    html = f.read()

prompt = "generate JS to remove the modal paywall, AND uncover the blurred out text. Include multiple elemenet modifications if you see more than one element involved. Here is html from the page please review it and come up with a relevant answer to this page contents only: " + html

url = "http://localhost:11434/api/generate"
payload = {
    "model": model,
    "prompt": prompt,
    "options": {
        "num_ctx": num_ctx,
        "stream": True
    }
}

headers = {'Content-Type': 'application/json'}

print("model: ", model, "num_ctx: ", num_ctx, "use_file: ", use_file, prompt_len:=len(prompt))
response = requests.post(url, data=json.dumps(payload), headers=headers, stream=True)

# Stream the response and print only the "response" part of the JSON
for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        json_line = json.loads(decoded_line)
        if "response" in json_line:
            print(json_line["response"], end='', flush=True)
