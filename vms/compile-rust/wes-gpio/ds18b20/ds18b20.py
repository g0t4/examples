# sudo apt install -y python3-libgpiod # for system packages, can this work in a venv?
#   seems like I might need apt to install deps for gpiod... version in venv doesn't work but then if I move out of venv it works
# https://pypi.org/project/gpiod/

import gpiod
import time
from gpiod.line import Direction, Value

CHIP = 'gpiochip0'
DS1820B_PIN = 12

# readability:
LOW = Value.INACTIVE
HIGH = Value.ACTIVE

# ! NOTE ABOUT gpiod pkg (in venv vs system pkgs):
# ! below uses gpiod via `pip install gpiod` via venv
# !   IS NOT same as gpiod pkg via `apt install apt info python3-libgpiod`
# research on diffs:
# system pkgs => python3 =>
#   import gpiod
#   gpiod.version_string() #  1.6.3
#   help(gpiod)   # completely diff APIs
#   gpiod # <module 'gpiod' from '/usr/lib/python3/dist-packages/gpiod.cpython-311-aarch64-linux-gnu.so'>
#
#   exit repl:
#       dpkg -S /usr/lib/python3/dist-packages/gpiod.cpython-311-aarch64-linux-gnu.so
#       # => python3-libgpiod:arm64: /usr/lib/python3/dist-packages/gpiod.cpython-311-aarch64-linux-gnu.so
#
# venv pkgs => python3 =>
#   import gpiod
#   gpiod.version.__version__ # 2.2.1
#   gpiod # <module 'gpiod' from '/home/pi/wes-gpio/.venv/lib/python3.11/site-packages/gpiod/__init__.py'>
#   help(gpiod)   # completely diff APIs
#
#
# IIUC, as of v2.0.2 they made breaking changes to the APIs that replaced the unofficial pure python APIS (must be the system pkg version b/c it is 1.6.3)... and going forward it sounds like the new APIs are via pypi pkg only (not apt installed cpython pkg)... I bet that is is, the cpython impl is probably not updated to 2.x b/c that would break reality, and so its left at that point in time and won't ever be migrated to 2.x... would make sense

def initialize_bus() -> bool:

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-init-bus",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=LOW)},
    ) as output:
        # initialize pulse is:
        #   480us low => release
        #   wait 15-60us for presence signal from sensor(s)
        #   presence signal (low) lasts 60us-240us
        time.sleep(480 / 1_000_000)  # 480us (max 960us)
        output.set_value(DS1820B_PIN, HIGH)

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="detect-presence",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)},
    ) as input:
        # wait for presence signal from sensor(s)
        start_time = time.time()
        while input.get_value(DS1820B_PIN) != LOW:
            if time.time() - start_time > 0.001:
                print("No presence signal")
                return False
        # print("Presence signal received")
        # wait for presence signal to end
        start_time = time.time()
        while input.get_value(DS1820B_PIN) == LOW:
            if time.time() - start_time > 0.001:
                print("Presence signal didn't end")
                return False
        # print("Presence signal ended")
        # sensor should now be sending data
        return True


def main():
    if (not initialize_bus()):
        print("Failed to initialize bus")
        return

    print("Bus initialized")


if __name__ == "__main__":
    main()
