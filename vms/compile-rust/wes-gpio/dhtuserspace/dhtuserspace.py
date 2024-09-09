import time
import gpiod # uses libgpiod which uses gpiod_ functions in the kernel in drivers/gpio/gpiolib.c (i.e. gpiod_request, gpiod_get_value, gpiod_set_value, etc.)
from gpiod.line import Direction, Value

LINE = 17

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
