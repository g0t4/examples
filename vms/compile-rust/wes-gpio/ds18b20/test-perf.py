import time


def get_time_us():
    return time.time() * 1_000_000


calls = 100

# warmup, after 100 calls the times looked as expected (time.time() fastest 0.28us, get_time_us() 0.32us, time.time() * 1_000_000 between the other two)
for i in range(100):
    test = time.time()
    test = get_time_us()
    # call both

start = get_time_us()
for i in range(calls):
    test = time.time()
end = get_time_us()
diff_us = (end - start)
per_call_us = diff_us / calls
print(f"time.time() took {per_call_us:.2f} us per call, total {diff_us:.2f} us")

start = get_time_us()
for i in range(calls):
    test = get_time_us()
end = get_time_us()
diff_us = (end - start)
per_call_us = diff_us / calls
print(f"get_time_us() took {per_call_us:.2f} us per call, total {diff_us:.2f} us")

# inline time.time() * 1_000_000
start = get_time_us()
for i in range(calls):
    test = time.time() * 1_000_000
end = get_time_us()
diff_us = (end - start)
per_call_us = diff_us / calls
print(f"time.time() * 1_000_000 took {per_call_us:.2f} us per call, total {diff_us:.2f} us")
