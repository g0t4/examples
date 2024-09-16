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


def initialize_bus() -> bool:
    # FYI below uses gpiod via `pip install gpiod`... which IS NOT same as gpiod pkg via `apt install apt info python3-libgpiod`

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
