# sudo apt install -y python3-libgpiod # for system packages, can this work in a venv?
#   seems like I might need apt to install deps for gpiod... version in venv doesn't work but then if I move out of venv it works
# https://pypi.org/project/gpiod/

# !!! TIMING MIGHT BE WORKING in my python!
# !!! ok my timing looks close enough now actually, so I might have smth wrong with the protocol, let's revisit that next ... I am within the tolerances I understand and still don't get a response to the read ROM... I bet I have smth off in my understanding
#  DO NOT BE SLOPPY with prints or anything that adds overhead... one print can add 50us, same with not carefully choosing when to drive line low (before/after requesting output mode)
# PRN might be able to keep a list of messages and dump on a failure/completino as long as adding to the list is trivial <1us timing
# !!! WES KEEP IN MIND timing might not work out in python still... c code would rock and you can have logging there that doesn't kill perf (i.e. pr_ dev_ printk_ in a module)

# FYI I checked out libgpiod for the APIs => https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.gitß => libgpiod/bindings/python

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
    precise_delay_us(3)  # when 2us (sometimes 1us not met b/c took a while to rise back)


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


def write_command_todo_split_read(command: int) -> bool:
    # write command is 0xcc (11001100)
    # response: 8-bit CRC

    # recovery time: min 1us (high, released)
    # write 0: 60us-120us low
    # write 1: 1us-15us low ( min 60us total slot)

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-command",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)},  # FYI CONFIRMED => keep it high for so any overhead in request line isn't adding to total time low on first bit if 0
            #   PREV defaulted to low and that added 50us to the first bit low time!!!!
    ) as line:
        bits = []
        # build bits so we can send in left to right order in next loop
        for i in range(8):
            bits = [(command >> i) & 1] + bits
        bits.reverse()  #! todo actually confirm...  I have my suspicions b/c when I reverse for READ ROM... I get inactive past when I release line so that is a response
        for bit in bits:
            if bit:
                # write 1
                line.set_value(DS1820B_PIN, LOW)
                precise_delay_us(2)  # min 1us, max <15us
                line.set_value(DS1820B_PIN, HIGH)
                precise_delay_us(60)  # 60 us total window (min)
            else:
                # write 0
                line.set_value(DS1820B_PIN, LOW)
                precise_delay_us(65)  # min 60us => wow turned into 120us (LA1010),73us, 68us, 72us ...  120us breaks the rules (max 120)... the rest work inadvertently
                line.set_value(DS1820B_PIN, HIGH)
                # PRN wait for it to be high? I am noticing that when I am low for along time and then go high, it seems to cut into recovery between bits
            wait_for_recovery_between_bits()
        print(f"sent command ROM read")  # delay here is NBD (can be infinite and still trigger read next)

        bits = []

        def read_bit():
            # ensure output so we can trigger read bit
            # PRN check direction before setting? might only matter on first byte and the overhead here is NBD as nothing timing matters until I pull low
            line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)})
            line.set_value(DS1820B_PIN, LOW)  # host starts the read by driving low for >1us but not long
            precise_delay_us(1)  # min time 1 us

            line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)})  # seems to take 5-10us... unpredictable :( crap
            start_time = time.time()  # TODO put this here or before delay 1us above?

            while line.get_value(DS1820B_PIN) == LOW:
                if time.time() - start_time > 1:
                    print("timeout - held low indefinitely - s/b NOT POSSIBLE")
                    return False
            end_time = time.time()
            seconds_low = end_time - start_time
            if seconds_low > 0.000_014:  # put back to 15us if move start_time before delay 1us
                bits.append(0)
                # print(f"low - {seconds_low*1_000_000} us")
            if seconds_low < 0.000_002:
                # looks like sensor never held it low past me so this is invalid
                print("timeout - sensor not holding low after I release - it is not responding to read request")
                return False
            else:
                bits.append(1)
                # print(f"high - {seconds_low*1_000_000} us")
            while time.time() - start_time < 0.000_060:
                # all read slots must be 60us (min)
                pass
            wait_for_recovery_between_bits()
            return True

        for i in range(64):
            if (not read_bit()):
                print(f"Failed to read bit {i}, aborting...")
                return False

        print(f"bits read: {bits}")
        bytes = []
        for i in range(0, 64, 8):
            byte = 0
            for j in range(8):
                byte = byte | (bits[i + j] << j)
            bytes.append(byte)

        # ! no doubt I think I have this all wrong for order:
        # *** see data sheet:
        #     Then starting with the least significant bit of the family code, 1 bit at a time is shifted in...
        #     are bits in reverse order within each byte?
        #
        #     | 8-BIT CRC CODE |  48-BIT SERIAL NUMBER | 8-BIT FAMILY CODE |
        #     |                |                       |       (28h)       |
        #     | MSB        LSB |  MSB              LSB | MSB           LSB |
        #
        print("bytes:")
        for byte in bytes:
            print(f"  {byte:08b} ({byte})")
            # YAY often I am seeing the same bits in each byte... 1st and 5th sometimes vary...

        family_code = bytes[0]  # 8 bits (1 byte)
        serial_number = bytes[1:7]  # 48 bits (6 bytes)
        crc = bytes[7]  # 8 bits (1 byte)
        print(f"Family code: {family_code}")
        print(f"Serial number: {serial_number}")
        print(f"CRC: {crc}")

    # ** wait/read_edge_events => my first attempt didn't work?!

    # bit = line.get_value(DS1820B_PIN)  # read the line to get the response
    # precise_delay_us(13)
    # bit_2 = line.get_value(DS1820B_PIN)  # read the line to get the response
    # print(f"bit read: {bit}, {bit_2}")  # ! OMG after bits.reverse() when I read I get inactive / active ( FYI active/active means sensor is not responding)

    #help(line)

    return True


# def read_bits(num_bits: int) -> bytes:
#     # read 0: 15us-60us low
#     # read 1: 1us-15us low
#     # recovery time: min 1us (high, released)

#     with gpiod.request_lines(
#             "/dev/gpiochip4",
#             consumer="read-bits",
#             config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT)},
#     ) as input:
#         bits = []
#         for i in range(num_bits):
#             # host has to trigger the read

#             # # wait for start of bit (low)
#             # timeout_start_time = time.time()
#             # while input.get_value(DS1820B_PIN) != LOW:
#             #     if time.time() - timeout_start_time > 1:
#             #         print(f"Timeout waiting for bit {i} low signal before high.")
#             #         return None

#             # start_time = time.time()

#             # timeout_start_time = time.time()
#             # while input.get_value(DS1820B_PIN) == LOW:
#             #     if time.time() - timeout_start_time > 1:
#             #         print(f"Timeout waiting for bit {i} high signal.")
#             #         return None

#             # # wait for end of bit (low)
#             # timeout_start_time = time.time()
#             # while input.get_value(DS1820B_PIN) != LOW:
#             #     if time.time() - timeout_start_time > 1:
#             #         print(f"Timeout waiting for bit {i} low signal after high.")
#             #         return None

#             # end_time = time.time()
#             # duration = end_time - start_time
#             # bits.append(1 if duration < 0.000015 else 0)

#         return bytes(bits)


def read_rom() -> bool:
    # read ROM command is 0x33 (110011)
    # response: 8-bit family code, unique 48-bit serial number, and 8-bit CRC

    commmand = 0x33  # DO I HAVE CMD RIGHT? or bit order right?
    if not write_command_todo_split_read(commmand):  # TODO pass line in so can reconfigure or is request just as fast? THERE HAS TO BE A FASTER way to change direction, my code was incredibly fast at that
        print("Failed to send ROM read command")
        return False
    # TODO ...
    return True


def main():

    if (not initialize_bus()):
        print("Failed to initialize bus")
        return
    print("Bus initialized")
    read_rom()


if __name__ == "__main__":
    main()
