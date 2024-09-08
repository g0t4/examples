import time
import gpiod
import matplotlib.pyplot as plt
import numpy as np
from gpiod.line import Direction, Value
from collections import deque

LINE = 4
SAMPLE_DURATION = 3  # seconds
SAMPLE_INTERVAL = 0.5  # seconds

# Deque to store the samples over time
samples = deque(maxlen=int(SAMPLE_DURATION / SAMPLE_INTERVAL))

with gpiod.request_lines(
    "/dev/gpiochip4",
    consumer="test-wes",
    config={
        LINE: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.ACTIVE
        )
    },
) as request:
    print(f"Initial value: {request.get_value(LINE)}")
    
    start_time = time.time()
    
    while True:
        current_time = time.time() - start_time
        
        # Toggle GPIO value
        request.set_value(LINE, Value.ACTIVE)
        active_value = request.get_value(LINE)
        print(f"Active value: {active_value}")
        samples.append((current_time, 1 if active_value == Value.ACTIVE else 0))
        time.sleep(SAMPLE_INTERVAL)
        
        request.set_value(LINE, Value.INACTIVE)
        inactive_value = request.get_value(LINE)
        print(f"Inactive value: {inactive_value}")
        samples.append((current_time, 1 if inactive_value == Value.ACTIVE else 0))
        time.sleep(SAMPLE_INTERVAL)

        # Check if we have three seconds' worth of samples and plot them
        if len(samples) == samples.maxlen:
            break

# Plot the samples
times, values = zip(*samples)  # Unpack times and values
plt.plot(times, values, marker='o')
plt.title(f"GPIO Line {LINE} Activity Over Time")
plt.xlabel("Time (s)")
plt.ylabel("GPIO Value")
plt.ylim(-0.1, 1.1)  # Values are 0 or 1
plt.show()
samples.clear()  # Clear the samples to start a new window
