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


def reset_bus_line(line):
    # initialize pulse is:
    #   480us low => release
    #   wait 15-60us for presence signal from sensor(s)
    #   presence signal (low) lasts 60us-240us

    line.set_value(DS1820B_PIN, LOW)
    precise_delay_us(480)  # 480us (max 960us) => MEASURED 545us!? (LA1010)
    line.set_value(DS1820B_PIN, HIGH)  # release

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
        prev_bit = 0
        this_bit = (command >> i) & 1
        cmd_bits = cmd_bits + [this_bit]  # append each bit to end of list
    for bit in cmd_bits:
        if bit:
            # write 1
            line.set_value(DS1820B_PIN, LOW)
            # TODO PRN read value until its actually low? then start timing?
            # min 1us, max <15us
            if prev_bit == 0:
                precise_delay_us(2)  # 0 => 1 needs less time to pull low again by not as high above threshold
            else:
                precise_delay_us(5)  # 1 => 1 needs more time to pull low b/c way above threshold
            # TODO tweak delay based on previous bit (current line status before set low) 1 => 1 needs more delay (pull down) whereas 0 => 1 needs less delay as its not fully pulled back up most likely so it pulls below threshold faster
            line.set_value(DS1820B_PIN, HIGH)
            precise_delay_us(60)  # 60 us total window (min)
            prev_bit = 1
        else:
            # write 0
            line.set_value(DS1820B_PIN, LOW)
            precise_delay_us(65)  # min 60us => wow turned into 120us (LA1010),73us, 68us, 72us ...  120us breaks the rules (max 120)... the rest work inadvertently
            line.set_value(DS1820B_PIN, HIGH)
            prev_bit = 0
            # PRN wait for it to be high? I am noticing that when I am low for along time and then go high, it seems to cut into recovery between bits
        wait_for_recovery_between_bits()
    print(f"sent command: {command:08b} ({hex(command)})")
    precise_delay_us(1000)
    return True


def read_rom_response(line) -> bool:

    response_bits = []

    for i in range(64):
        if (not read_bit(line, response_bits)):
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


def read_bit(line, response_bits) -> bool:
    # line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)}) # don't need to reconfigure
    line.set_value(DS1820B_PIN, HIGH)  # added after removing reconfigure b/c w/o this reading fails

    # PRN check direction before setting? might only matter on first byte and the overhead here is NBD as nothing timing matters until I pull low
    line.set_value(DS1820B_PIN, LOW)  # host starts the read by driving low for >1us but not long
    start_time = time.time()  # starts after pull low, have up to 15us to read the bit 0/1 for sure though I am seeing 31ish us for 0s, <5us for 1s
    precise_delay_us(1)  # min time 1 us

    # FYI using reconfigure is adding 7-8us of time before 1's can be read so that is bad news here... driving high works fine
    line.set_value(DS1820B_PIN, HIGH)  # fastest response times (~5us for read 1)
    # line.reconfigure_lines({DS1820B_PIN: gpiod.LineSettings(direction=Direction.INPUT)})  # adds (~12+ us for read 1, ouch)
    # FYI sensor also pulls low by this time so me releasing (set high) doesn't change it until sensor also releases

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


def read_scratchpad_response(line) -> bool:
    # TODO later extract common logic with other read response functions

    num_bytes = 9  # TODO last is CRC (this is always the case, right?)
    num_bits = num_bytes * 8
    response_bits = []

    for i in range(num_bits):
        if (not read_bit(line, response_bits)):
            print(f"Failed to read bit {i}, aborting...")
            return False

    all_bytes = []
    for i in range(0, num_bits, 8):
        byte = 0
        for j in range(8):
            byte = byte | (response_bits[i + j] << j)
        all_bytes.append(byte)

    print("bytes:")
    for byte in all_bytes:
        print(f"  {byte:08b} ({byte})")
        # YAY often I am seeing the same bits in each byte... 1st and 5th sometimes vary...

    # Define the CRC-8 function using the polynomial 0x131 (x^8 + x^5 + x^4 + 1)
    crc_all = ds18b20_crc8(bytes(all_bytes))  # if include last byte then it should come out to 0, no need to know CRC computed vs actual if they don't match anyways
    if crc_all != 0:
        print(f"Failed CRC check: {crc_all}")
        return False

    # TODO parse the scratchpad data for temp! IIUC first two or last two bytes are 16 bits of temp data but only 12 bit default precision + 1 sign bit (MSB)
    # MEMORY LAYOUT:
    #   0: Temp LSB
    #   1: Temp MSB
    #   2: Temp Alarm High
    #   3: Temp Alarm Low
    #   4: Configuration register
    #   5: Reserved
    #   6: Reserved
    #   7: Reserved
    #   8: CRC
    temp_lsb = all_bytes[0]
    temp_msb = all_bytes[1]
    temp_raw = (temp_msb << 8) | temp_lsb
    # stored in 16 bit sign extended two's complement
    #
    # 2^3 2^2 2^1 2^0 2^-1 2^-2 2^-3 2^-4 # LSB
    # S   S   S   S   S    2^6  2^5  2^4 # MSB
    #
    # positive numbers are verbatim in the 16 bits
    if temp_raw & 0x8000:
        # negative numbers are stored in two's complement form
        temp_raw = -((temp_raw ^ 0xFFFF) + 1)
    # all cases, 4 bits of decimal precision:
    temp_celsius = temp_raw / 16
    print(f"Temp: {temp_celsius:.2f}°C")
    temp_fahrenheit = temp_celsius * 9 / 5 + 32
    print(f"Temp: {temp_fahrenheit:.2f}°F")


def wait_for_temp_conversion_to_complete(line):
    # FYI lower response times for lower precision temps...
    #   9-bit => 93.75ms
    #   10-bit => 187.5ms
    #   11-bit => 375ms
    #   12-bit => 750ms

    # ! TODO dont hard code delay, use read ... why is it finnicky to the reset?!
    time.sleep(1)
    return True

    # issue read slot to get temp conversion status
    # conversion can take up to 750ms (12-bit precision)
    # FYI I find it takes ~500ms to for the conversion to complete

    # # in testing, if I don't add this delay, the first read bit is 1 which is almost as if the conversion didn't start yet...
    precise_delay_us(25_000)  # add at least 1000 delay before attempt read status...  in my testing...

    timeout_start = time.time()
    while True:
        response_bits = []
        if not read_bit(line, response_bits):  # read slot,  if 0 response then still copying, if 1 then done
            logger.error("Failed to read bit for status of temp conversion, aborting...")
            return False
        if response_bits[0] == 1:
            break
        if time.time() - timeout_start > 1:  # allow up to 1s (max is 750ms according to data sheet)
            logger.error("Timeout waiting for temp conversion to complete")
            return False
        precise_delay_us(50_000)  # check every 50ms

    print(f"Temp conversion complete after {time.time() - timeout_start:.2f} seconds")
    return True


# command constants
ROM_READ_CMD = 0x33
ROM_SKIP_CMD = 0xCC
CONVERT_T_CMD = 0x44
READ_SCRATCHPAD_CMD = 0xBE

# THIS IS MY VIDEO today => practical AI use case... let AI lookup values and just confirm them for you...  fill out this list (see page 14/27 for more cmds)


def full_read_rom(line):
    return send_command(line, ROM_READ_CMD) \
        and read_rom_response(line)


def skip_rom(line):
    return send_command(line, ROM_SKIP_CMD)


def read_rom_then_temp(line):
    # must issue ROM command before memory command
    #   in this case, use read ROM before issue convert T to capture temp to scratchpad
    #   then skip rom before reading scratchpad (temp)
    return reset_bus_line(line) \
        and full_read_rom(line) \
        and send_command(line, CONVERT_T_CMD) \
        and wait_for_temp_conversion_to_complete(line) \
        and reset_bus_line(line) \
        and skip_rom(line) \
        and send_command(line, READ_SCRATCHPAD_CMD) \
        and read_scratchpad_response(line)


def read_temp_with_skip_rom(line) -> bool:
    # assume only one ROM on the bus
    return reset_bus_line(line) \
        and skip_rom(line) \
        and send_command(line, CONVERT_T_CMD) \
        and wait_for_temp_conversion_to_complete(line) \
        and reset_bus_line(line) \
        and skip_rom(line) \
        and send_command(line, READ_SCRATCHPAD_CMD) \
        and read_scratchpad_response(line)


def read_power_supply_type(line):
    response_bits = []
    worked =  reset_bus_line(line) \
        and skip_rom(line) \
        and send_command(line, 0xB4) \
        and read_bit(line, response_bits)
    if not worked:
        print("Failed to read power supply type")
        return False
    if response_bits[0] == 0:
        # TODO hook up VDD to GND and try to see if returns parasite power supply (could be issues with parasitic power in terms of timing/pull-up power but I don't think it s/b a problem)
        print("Parasite power supply")
    else:
        print("External power supply")


def main():
    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="send-command",
            config={DS1820B_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=HIGH)},  # FYI CONFIRMED => keep it high for so any overhead in request line isn't adding to total time low on first bit if 0
            #   PREV defaulted to low and that added 50us to the first bit low time!!!!
    ) as line:
        # read_temp_with_skip_rom(line)
        read_rom_then_temp(line)
        # read_power_supply_type(line)


if __name__ == "__main__":
    main()

# NOTES
# ** wait/read_edge_events => my first attempt didn't work?! are these a superior interface?
