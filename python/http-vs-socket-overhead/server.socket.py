import socket
import threading

response = '{"matches": [{"score": 0.9255905151367188, "text": "local M = {}\\n\\nfunction M.add(a, b)\\n    messages\\n    return a + b\\nend\\n\\n\\n\\nreturn M", "file": "lua/ask-openai/prediction/tests/calc/calc.lua", "start_line": 1, "end_line": 10, "type": "raw", "rank": 1}, {"score": 0.8957789540290833, "text": "local M = {}\\n\\nfunction M.add(a, b)\\n    return a + b\\nend\\n\\nfunction M.sub(a, b)\\n    return a - b\\nend\\n\\nfunction M.mul(a, b)\\n    return a * b\\nend\\n\\nfunction M.div(a, b)\\n    if b == 0 then\\n        error(\\"Cannot divide by zero\\")\\n    end\\n    return a / b\\nend", "file": "lua/ask-openai/prediction/tests/calc/calc-from-14b-q8-way-further-coherent.lua", "start_line": 1, "end_line": 20, "type": "raw", "rank": 2}, {"score": 0.8584036827087402, "text": "}\\n\\nreturn M", "file": "lua/ask-openai/backends/models/agentica.lua", "start_line": 31, "end_line": 33, "type": "raw", "rank": 3}]}'

# FYI test with:
# echo -n 'query' | socat - TCP:localhost:9999

def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(1)
    while True:
        conn, _ = server.accept()
        _ = conn.recv(1024).decode()
        conn.send(response.encode())
        conn.close()

def main():
    start_socket_server()

if __name__ == "__main__":
    main()
