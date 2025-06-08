import httpx

url = "http://ollama:11434/api/generate"
headers = {'content-type': 'application/json'}
with open('./manual-tests/qwen3-001/02/prompt.txt', 'r') as f:
    prompt_content = f.read()
data = {
    "model": "qwen3:8b",
    "prompt": prompt_content,
    "stream": False,
    "think": False, # new in ollama, equiv of /nothink... this isn't working?!
    "options": {
        # "temperature": .2,
        # "top_p": .95,
    }
}

res = httpx.post(url, headers=headers, json=data, timeout=None)
#%%

json = res.json()
print(json['response'])

#%% 

# save to disk
with open('./manual-tests/qwen3-001/02/response02.txt', 'w') as f:
    f.write(json['response'])
