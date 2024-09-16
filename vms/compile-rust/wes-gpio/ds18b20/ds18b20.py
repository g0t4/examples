# sudo apt install -y python3-libgpiod # for system packages, can this work in a venv?
#   seems like I might need apt to install deps for gpiod... version in venv doesn't work but then if I move out of venv it works
# https://pypi.org/project/gpiod/

# !!! TIMING MIGHT BE WORKING in my python!
# !!! ok my timing looks close enough now actually, so I might have smth wrong with the protocol, let's revisit that next ... I am within the tolerances I understand and still don't get a response to the read ROM... I bet I have smth off in my understanding
#  DO NOT BE SLOPPY with prints or anything that adds overhead... one print can add 50us, same with not carefully choosing when to drive line low (before/after requesting output mode)
# PRN might be able to keep a list of messages and dump on a failure/completino as long as adding to the list is trivial <1us timing
# !!! WES KEEP IN MIND timing might not work out in python still... c code would rock and you can have logging there that doesn't kill perf (i.e. pr_ dev_ printk_ in a module)

# FYI I checked out libgpiod for the APIs => https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.gitß => libgpiod/bindings/python

import logging
import math
import gpiod
import time
from gpiod.line import Direction, Value

import crcmod  # ~1ms

ds18b20_crc8 = crcmod.mkCrcFun(0x131, initCrc=0, xorOut=0)  # ~0.250us, so only do it once... this is reusable right?

CHIP = 'gpiochip0'
DS1820B_PIN = 12

# readability:
LOW = Value.INACTIVE
HIGH = Value.ACTIVE

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

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
    # PRN address clock updates/corrections => only when I detect it as a problem
    # time.sleep is WAY off... hundreds of us in the LA1010 waveform
    start = time.perf_counter()
    while (time.perf_counter() - start) < (us / 1_000_000):
        pass


def wait_for_recovery_between_bits():
    precise_delay_us(3)  # when 2us (sometimes 1us not met b/c took a while to rise back)


def initialize_bus() -> bool:

    # PRN pull high initially and wait Xus to be sure it was high before we pull low?
    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-init-bus",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=LOW)},
    ) as line:
        # initialize pulse is:
        #   480us low => release
        #   wait 15-60us for presence signal from sensor(s)
        #   presence signal (low) lasts 60us-240us

        precise_delay_us(480)  # 480us (max 960us) => MEASURED 545us!? (LA1010)
        line.set_value(DS1820B_PIN, HIGH)

        # poll for presence signal from sensor(s)
        timeout_start_time = time.time()
        while line.get_value(DS1820B_PIN) != LOW:
            if time.time() - timeout_start_time > 0.000_100:  # timeout after 100us b/c should start w/in 15-60us
                logger.error("Presence signal not received")
                return False

        # poll for presence signal to end
        timeout_start_time = time.time()
        while line.get_value(DS1820B_PIN) == LOW:
            if time.time() - timeout_start_time > 0.001:
                logger.error("Presence signal did not end")
                return False

        # wait at least 480us for entirety of presence command + recovery time
        us_since_presence_start = math.floor((time.time() - timeout_start_time) * 1_000_000)
        precise_delay_us(480 - us_since_presence_start)  # wait for 480us total

        return True


def send_command(line, command) -> bool:
    # TODO written for READ ROM command, might need to make changes or other versions for other CMDs

    cmd_bits = []
    # TODO scope the waverform after no comms for a while, seems to initially have failed read rom... and then works after that first round... see if maybe line was not high or?
    # build bits so we can send in left to right order in next loop
    for i in range(8):
        # bits are sent in reverse (confirmed w/ protocol analyzer on LA1010 which successfully matched my READ ROM 0x33 command => )
        this_bit = (command >> i) & 1
        cmd_bits = cmd_bits + [this_bit]  # append each bit to end of list
    for bit in cmd_bits:
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
    print(f"sent command: {command:08b} ({hex(command)})")
    return True


def read_rom_response(line) -> bool:

    response_bits = []

    def read_bit():
        # line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)}) # don't need to reconfigure
        line.set_value(DS1820B_PIN, HIGH)  # added after removing reconfigure b/c w/o this reading fails

        # PRN check direction before setting? might only matter on first byte and the overhead here is NBD as nothing timing matters until I pull low
        line.set_value(DS1820B_PIN, LOW)  # host starts the read by driving low for >1us but not long
        start_time = time.time()  # starts after pull low, have up to 15us to read the bit 0/1 for sure though I am seeing 31ish us for 0s, <5us for 1s
        precise_delay_us(1)  # min time 1 us

        # FYI using reconfigure is adding 7-8us of time before 1's can be read so that is bad news here... driving high works fine
        line.set_value(DS1820B_PIN, HIGH)  # fastest response times (~5us for read 1)
        # line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)})  # adds (~12+ us for read 1, ouch)

        while line.get_value(DS1820B_PIN) == LOW:
            if time.time() - start_time > 1:
                logger.error("timeout - held low indefinitely - s/b NOT POSSIBLE")
                return False
        end_time = time.time()
        seconds_low = end_time - start_time
        if seconds_low > 0.000_015:
            response_bits.append(0)
        elif seconds_low < 0.000_002:
            # looks like sensor never held it low past me so this is invalid
            logger.error("timeout - sensor not holding low after I release - it is not responding to read request")
            return False
        else:
            response_bits.append(1)
        while time.time() - start_time < 0.000_080:  # TODO did increasing this make reads more reliable? (60us required minimum)
            # all read slots must be 60us (min)
            pass
        wait_for_recovery_between_bits()
        return True

    for i in range(64):
        if (not read_bit()):
            print(f"Failed to read bit {i}, aborting...")
            return False

    print(f"bits read: {response_bits}")
    all_bytes = []
    for i in range(0, 64, 8):
        byte = 0
        for j in range(8):
            byte = byte | (response_bits[i + j] << j)
        all_bytes.append(byte)

    # *** see data sheet:
    #     Then starting with the least significant bit of the family code, 1 bit at a time is shifted in...
    #     are bits in reverse order within each byte?
    #
    #     | 8-BIT CRC CODE |  48-BIT SERIAL NUMBER | 8-BIT FAMILY CODE |
    #     |                |                       |       (28h)       |
    #     | MSB        LSB |  MSB              LSB | MSB           LSB |
    #
    print("bytes:")
    for byte in all_bytes:
        print(f"  {byte:08b} ({byte})")
        # YAY often I am seeing the same bits in each byte... 1st and 5th sometimes vary...

    # Define the CRC-8 function using the polynomial 0x131 (x^8 + x^5 + x^4 + 1)
    crc_all = ds18b20_crc8(bytes(all_bytes))  # if include last byte then it should come out to 0, no need to know CRC computed vs actual if they don't match anyways
    if crc_all != 0:
        print(f"Failed CRC check: {crc_all}")
        return False

    family_code = all_bytes[0]  # 8 bits (1 byte)
    serial_number = all_bytes[1:7]  # 48 bits (6 bytes)
    crc = all_bytes[7]  # 8 bits (1 byte)
    logger.info(f"Serial number: {serial_number}")
    logger.info(f"CRC: {crc}")
    if family_code != 0x28:
        print(f"Invalid family code: {hex(family_code)}, expected 0x28")
        return False

    return True


def wait_for_temp_conversion_to_complete(line):
    timeout_start_time = time.time()
    while line.get_value(DS1820B_PIN) == LOW:
        if time.time() - timeout_start_time > 1:
            logger.error("Temp conversion did not complete after 1sec")
            return False
    return True


ROM_READ_CMD = 0x33
CONVERT_T_CMD = 0x44
READ_SCRATCHPAD_CMD = 0xBE
# THIS IS MY VIDEO today => practical AI use case... let AI lookup values and just confirm them for you...  fill out this list (see page 14/27 for more cmds)


def test_read_temp() -> bool:

    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-command",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)},  # FYI CONFIRMED => keep it high for so any overhead in request line isn't adding to total time low on first bit if 0
            #   PREV defaulted to low and that added 50us to the first bit low time!!!!
    ) as line:
        return send_command(line, ROM_READ_CMD)  \
            and read_rom_response(line) \
            and send_command(line, CONVERT_T_CMD) \
            and wait_for_temp_conversion_to_complete(line)


def main():

    if (not initialize_bus()):
        print("Failed to initialize bus")
        return
    print("Bus initialized")
    test_read_temp()


if __name__ == "__main__":
    main()

# NOTES
# ** wait/read_edge_events => my first attempt didn't work?! are these a superior interface?
