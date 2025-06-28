import asyncio

from fastapi import FastAPI
from uvicorn import Config, Server

app = FastAPI()

response = '{"matches": [{"score": 0.9255905151367188, "text": "local M = {}\\n\\nfunction M.add(a, b)\\n    messages\\n    return a + b\\nend\\n\\n\\n\\nreturn M", "file": "lua/ask-openai/prediction/tests/calc/calc.lua", "start_line": 1, "end_line": 10, "type": "raw", "rank": 1}, {"score": 0.8957789540290833, "text": "local M = {}\\n\\nfunction M.add(a, b)\\n    return a + b\\nend\\n\\nfunction M.sub(a, b)\\n    return a - b\\nend\\n\\nfunction M.mul(a, b)\\n    return a * b\\nend\\n\\nfunction M.div(a, b)\\n    if b == 0 then\\n        error(\\"Cannot divide by zero\\")\\n    end\\n    return a / b\\nend", "file": "lua/ask-openai/prediction/tests/calc/calc-from-14b-q8-way-further-coherent.lua", "start_line": 1, "end_line": 20, "type": "raw", "rank": 2}, {"score": 0.8584036827087402, "text": "}\\n\\nreturn M", "file": "lua/ask-openai/backends/models/agentica.lua", "start_line": 31, "end_line": 33, "type": "raw", "rank": 3}]}'

@app.get("/query")
async def http_query():
    return response

async def start_fastapi_server():
    config = Config(app=app, host="localhost", port=8000, log_level="critical")
    server = Server(config)
    await server.serve()

def main():
    asyncio.run(start_fastapi_server())

if __name__ == "__main__":
    main()
