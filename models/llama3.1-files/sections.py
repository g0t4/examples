import requests
import json

# model = "llama3"
# model = "mistral-nemo" # handles 1to7.md like llama3.1
num_ctx = 8192
model = "llama3.1:8b"
#num_ctx = 10240 # 10k tokens
#model = "llama3.1:70b"
#num_ctx = 131072

# read 1to4.md into a propmt string:
use_file = "1to4.md" # 4.5k tokens
# use_file = "5to9.md" # 4.5k tokens
# use_file = "all.md" # just over 9k tokens
# use_file = "1to7.md" # just under 8k tokens
with open(use_file, "r") as f:
    markdown = f.read()

prompt = "list the top level sections (line starts with ## Section) from this markdown file, do not elaborate: " + markdown

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

print("model: ", model, "num_ctx: ", num_ctx, "use_file: ", use_file)
response = requests.post(url, data=json.dumps(payload), headers=headers, stream=True)

# Stream the response and print only the "response" part of the JSON
for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        json_line = json.loads(decoded_line)
        if "response" in json_line:
            print(json_line["response"], end='', flush=True)
