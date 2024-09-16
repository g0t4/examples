# sudo apt install -y python3-libgpiod # for system packages, can this work in a venv?
#   seems like I might need apt to install deps for gpiod... version in venv doesn't work but then if I move out of venv it works
# https://pypi.org/project/gpiod/

#!!! deal breaker it seems is sleeping in python, the accuracy isn't working out... and it might be due to overhead from interpreting commands... i.e. attempt wait 480us... but it is 545us! off by 65 us when I need 1us (or less) precision... I might need to switch to c code to get better timing... why would it be off by 65us?! I can't afford that tolerance... can I fix anything to make the python work or is it just not possible w/ interpreted... can I compile my python code? or?

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
#
#
# I do know the examples in the pypi page (https://pypi.org/project/gpiod/) show using request_lines so def aligns with the fact that I s/b using venv for the following request_lines usages:

import time


def precise_delay_us(us):
    # time.sleep is WAY off... hundreds of us in the LA1010 waveform
    start = time.perf_counter()
    while (time.perf_counter() - start) < (us / 1_000_000):
        pass


def wait_for_recovery_between_bits():
    precise_delay_us(2)  # min 1us (high, released)


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
        precise_delay_us(480)  # 480us (max 960us) => MEASURED 545us!? (LA1010) 
        #  I might need to switch to c code to get better timing... why would it be off by 65us?! I can't afford that tolerance
        output.set_value(DS1820B_PIN, HIGH)

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="detect-presence",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)},
    ) as input:
        # wait for presence signal from sensor(s)
        timeout_start_time = time.time()
        while input.get_value(DS1820B_PIN) != LOW:
            if time.time() - timeout_start_time > 0.001:
                print("No presence signal")
                return False
        # print("Presence signal received")
        # wait for presence signal to end
        timeout_start_time = time.time()
        while input.get_value(DS1820B_PIN) == LOW:
            if time.time() - timeout_start_time > 0.001:
                print("Presence signal didn't end")
                return False
        # IIUC must wait at least 480us for entirety of presence command + recovery time
        precise_delay_us(480)  # should work IIUC # TODO ok? s/b ok to wait longer than needed
        # precse_delay_us(480 - (time.time() - timeout_start_time)*1_000_000)  # take off time already spent for presence low?
        # # print("Presence signal ended")
        # sensor should now be sending data
        return True


def write_command(command: int) -> bool:
    # write command is 0xcc (11001100)
    # response: 8-bit CRC

    # recovery time: min 1us (high, released)
    # write 0: 60us-120us low
    # write 1: 1us-15us low

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-command",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT)},
    ) as output:
        bits = []
        # build bits so we can send in left to right order in next loop
        for i in range(8):
            bits = [(command >> i) & 1] + bits

        for bit in bits:
            if bit:
                # write 1
                print(f"writing 1")
                output.set_value(DS1820B_PIN, LOW)
                precise_delay_us(2)  # min 1us, max <15us
                output.set_value(DS1820B_PIN, HIGH)
                precise_delay_us(58)  # 58us of 60us total min IIUC
            else:
                # write 0
                print(f"writing 0")
                output.set_value(DS1820B_PIN, LOW)
                precise_delay_us(65)  # min 60us
                output.set_value(DS1820B_PIN, HIGH)
            wait_for_recovery_between_bits()
        print(f"sent command ROM read")
        return True


def read_bits(num_bits: int) -> bytes:
    # read 0: 15us-60us low
    # read 1: 1us-15us low
    # recovery time: min 1us (high, released)

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="read-bits",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)},
    ) as input:
        bits = []
        for i in range(num_bits):
            # wait for start of bit (low)
            timeout_start_time = time.time()
            while input.get_value(DS1820B_PIN) != LOW:
                if time.time() - timeout_start_time > 0.001:
                    print(f"Timeout waiting for bit {i} low signal before high.")
                    return None

            start_time = time.time()

            timeout_start_time = time.time()
            while input.get_value(DS1820B_PIN) == LOW:
                if time.time() - timeout_start_time > 0.001:
                    print(f"Timeout waiting for bit {i} high signal.")
                    return None

            # wait for end of bit (low)
            timeout_start_time = time.time()
            while input.get_value(DS1820B_PIN) != LOW:
                if time.time() - timeout_start_time > 0.001:
                    print(f"Timeout waiting for bit {i} low signal after high.")
                    return None

            end_time = time.time()
            duration = end_time - start_time
            bits.append(1 if duration < 0.000015 else 0)

        return bytes(bits)


def read_rom() -> bool:
    # read ROM command is 0x33 (110011)
    # response: 8-bit family code, unique 48-bit serial number, and 8-bit CRC

    # recovery time: min 1us (high, released)
    # write 0: 60us-120us low
    # write 1: 1us-15us low
    # read 0: 15us-60us low
    # read 1: 1us-15us low
    commmand = 0x33
    if not write_command(commmand):
        print("Failed to send ROM read command")
        return False

    bytes = read_bits(64)
    if bytes is None:
        print("Failed to read ROM")
        return False

    # see Figure 4 for ordering of bytes... CRC comes first IIUC
    crc = bytes[0]  # 8 bits (1 byte) (sent first?)
    serial_number = bytes[1:7]  # 48 bits (6 bytes)
    family_code = bytes[7]  # 8 bits (1 byte) (sent last?)
    print(f"Family code: {family_code}")
    print(f"Serial number: {serial_number}")
    print(f"CRC: {crc}")
    family_code_hex = family_code.to_bytes(1, byteorder='big').hex()
    serial_number_hex = serial_number.hex()
    crc_hex = crc.to_bytes(1, byteorder='big').hex()
    print(f"Family code (hex): {family_code_hex}")
    print(f"Serial number (hex): {serial_number_hex}")
    print(f"CRC (hex): {crc_hex}")


def main():
    if (not initialize_bus()):
        print("Failed to initialize bus")
        return
    print("Bus initialized")
    if (not read_rom()):
        print("Failed to read ROM")
        return
    print("ROM read")
    # if (not read_scratchpad()):
    #     print("Failed to read scratchpad")
    #     return


if __name__ == "__main__":
    main()
