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
        config={LINE: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},
) as request:
    print(f"Initial value: {request.get_value(LINE)}")


    plt.ion()  # Enable interactive mode for real-time updates
    fig, ax = plt.subplots()
    line, = ax.plot([], [], marker='o')  # Initialize an empty line
    ax.set_xlim(0, SAMPLE_DURATION)
    ax.set_ylim(-0.1, 1.1)
    ax.set_title(f"GPIO Line {LINE} Activity Over Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("GPIO Value")

    times = []
    values = []

    start_time = time.time()

    while True:
        current_time = time.time() - start_time

        # Toggle GPIO value
        request.set_value(LINE, Value.ACTIVE)
        active_value = request.get_value(LINE)
        print(f"Active value: {active_value}")
        times.append(current_time)
        values.append(1 if active_value == Value.ACTIVE else 0)

        line.set_xdata(times)
        line.set_ydata(values)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        plt.pause(0.01)  # Pause briefly to allow the plot to update
        time.sleep(SAMPLE_INTERVAL)

        request.set_value(LINE, Value.INACTIVE)
        inactive_value = request.get_value(LINE)
        print(f"Inactive value: {inactive_value}")
        current_time = time.time() - start_time
        times.append(current_time)
        values.append(1 if inactive_value == Value.ACTIVE else 0)

        line.set_xdata(times)
        line.set_ydata(values)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        plt.pause(0.01)  # Pause briefly to allow the plot to update
        time.sleep(SAMPLE_INTERVAL)

        # Check if we have three seconds' worth of samples and stop
        if current_time >= SAMPLE_DURATION:
            break

plt.ioff()  # Turn off interactive mode
plt.show()  # Display the final plot
