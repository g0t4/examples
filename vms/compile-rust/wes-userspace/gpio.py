import time
import gpiod # uses libgpiod which uses gpiod_ functions in the kernel in drivers/gpio/gpiolib.c (i.e. gpiod_request, gpiod_get_value, gpiod_set_value, etc.)
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

# FYI IIUC, kernel has:
#   gpio.h => with gpio_ functions  (usess global line numbers using base offsets)
#   gpio_v2_* functions (uses device + line number, IIUC)
#   gpiolib.c => gpiod_* functions (uses device + line number, IIUC)
#
# userspace:
#   libgpiod => uses gpiod_* functions
#   chardev (via sysfs)
#   sysfs legacy gpio interface (deprecated) => uses gpio_ functions