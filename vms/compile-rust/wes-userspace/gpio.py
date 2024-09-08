import time
import gpiod
from gpiod.line import Direction, Value

LINE = 4

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
    while True:
        request.set_value(LINE, Value.ACTIVE)
        print(f"Current value: {request.get_value(LINE)}")
        time.sleep(1)
        request.set_value(LINE, Value.INACTIVE)
        print(f"Current value: {request.get_value(LINE)}")
        time.sleep(1)

# CRUCIAL for user space programs, I need access to GPIO w/o sudo...
# sudo usermod -aG gpio $USER