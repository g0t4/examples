import socket
import time

import requests

def benchmark_socket(n_requests=1000):
    start_time = time.time()
    for _ in range(n_requests):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9999))
        sock.send("query".encode())
        sock.recv(8192)
        sock.close()
    return time.time() - start_time

def benchmark_http(n_requests=1000):
    start_time = time.time()
    for _ in range(n_requests):
        _ = requests.get("http://localhost:8000/query")
        # print(f"Response: {_.text}")
    return time.time() - start_time

def main():
    socket_time = benchmark_socket()
    http_time = benchmark_http()

    print(f"Socket: {socket_time:.4f} seconds")
    print(f"HTTP(fastapi): {http_time:.4f} seconds")
    print(f"HTTP overhead: {(http_time/socket_time)*100:.2f}%")

if __name__ == "__main__":
    main()
