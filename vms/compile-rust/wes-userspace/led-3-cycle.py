import time
import gpiod  # uses libgpiod which uses gpiod_ functions in the kernel in drivers/gpio/gpiolib.c (i.e. gpiod_request, gpiod_get_value, gpiod_set_value, etc.)
from gpiod.line import Direction, Value

LINE17 = 17
LINE27 = 27  # right below 17
LINE22 = 22  # right below 27

with gpiod.request_lines(
        "/dev/gpiochip4",
        consumer="test-wes",
        config={
            LINE17: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
            LINE27: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
            LINE22: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
        },
) as request:
    print(f"Initial values: {request.get_value(LINE17)} {request.get_value(LINE27)} {request.get_value(LINE22)}")
    while True:
        request.set_value(LINE17, Value.ACTIVE)
        request.set_value(LINE27, Value.INACTIVE)
        request.set_value(LINE22, Value.INACTIVE)
        print(f"Current values: {request.get_value(LINE17)} {request.get_value(LINE27)} {request.get_value(LINE22)}")
        time.sleep(1)

        request.set_value(LINE17, Value.INACTIVE)
        request.set_value(LINE27, Value.ACTIVE)
        request.set_value(LINE22, Value.INACTIVE)
        print(f"Current values: {request.get_value(LINE17)} {request.get_value(LINE27)} {request.get_value(LINE22)}")
        time.sleep(1)

        request.set_value(LINE17, Value.INACTIVE)
        request.set_value(LINE27, Value.INACTIVE)
        request.set_value(LINE22, Value.ACTIVE)
        print(f"Current values: {request.get_value(LINE17)} {request.get_value(LINE27)} {request.get_value(LINE22)}")
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
