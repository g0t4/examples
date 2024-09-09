import gpiod
import time
from gpiod.line import Direction, Value

TIMEOUT_SEC = 2  # Timeout in seconds
MAX_WAIT = 0.2  # Maximum time to wait for signal in seconds

LINE = 17

# readability:
LOW = Value.INACTIVE
HIGH = Value.ACTIVE


def send_start_signal_to_AM2302():
    with gpiod.request_lines(
            "/dev/gpiochip4",
            consumer="dht22-output",
            config={LINE: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=LOW)},
    ) as request:
        # request.set_value(LINE, LOW)  # TODO do I need this if I already set output low in the config above?
        time.sleep(0.0008)  # Wait for at least 18 ms # pdf says 800us (minimum) => how about 2ms...
        # once I dropped to 400us instead of 2_000us (or even 800us)... at 400us I got valid bytes (including parity) and temp/humidity were in expected ranges!!! I thought to do this because... I figured maybe I am pulling low too long and missing the first bit(s)... once I dropped to 1_000us I started to see 77us in low response indicating I am shifting in the right direction... IIUC what I was thinking... anyways, let's just try this
        # 400us worked on sensor1 consistently, but sensor2 only works 20% of time?
        #   sensor1 is reliably working at 480us too... maybe sensor2 is dud? could explain trouble I have had with it?
        #     OR MAYBE NUKE my pull up resistor externally?
        #    don't forget 2 second min between samples...
        request.set_value(LINE, HIGH)
        # time.sleep(40 / 1_000_000)  # keep high for 20-40us # pdf doesn't give timing here so wtf am I doing waiting 40us?!


def read_sensor_bits():
    data = []
    times = []  # !! AWESOME TIMINGS are looking close to accurate! consistent up until those last few bits... hrm.. at least I am getting 38 bits with right patterns (43us ish for low period, 25us for 0 bit, 70us for 1 bit ... it is looking mostly good)

    # Switch the line to input mode to read data from the sensor
    with gpiod.request_lines("/dev/gpiochip4", consumer="dht22-input", config={LINE: gpiod.LineSettings(direction=Direction.INPUT)}) as request:

        def wait_for_edge_to(expected_value: Value, timeout, label=""):
            """Wait for a change in the signal line to the expected value."""
            start_time = time.time()
            while request.get_value(LINE) != expected_value:
                if time.time() - start_time > timeout:
                    return False
            total_us = (time.time() - start_time) * 1_000_000
            times.append(f"{label}: {total_us:.1f}us ({expected_value})")
            return True

        def dump_data():
            print(f"data: {data}")

            num_complete_bits = len(data) // 8
            complete_bits = data[:num_complete_bits * 8]
            complete_bytes = bits_to_bytes(complete_bits)
            print(f"Data so far: {complete_bytes}")

            humidity = get_humidity(complete_bytes)
            temperature = get_temperature(complete_bytes)
            print(f"Humidity: {humidity:.1f}%")
            print(f"Temperature: {temperature:.1f}°C, {temperature * 9 / 5 + 32:.1f}°F")

            print("Times:")
            for t in times:
                print(t)

        # Wait for the sensor to pull the line low, then high (response signal)
        if not wait_for_edge_to(LOW, MAX_WAIT, "initial low"):
            # ~80us (confirmed 77us which is about right for delays in requesting the line since set high)
            print("Sensor didn't respond with initial low signal.")
            return None
        # 80us low

        if not wait_for_edge_to(HIGH, MAX_WAIT, "initial high (s/b 80us)"):
            # FYI I am not seeing 80us here, rather 36us
            print("Sensor didn't pull the line high after initial low.")
            return None
        # 80us high

        # Sensor should now start sending 40 bits of data (5 bytes)
        for i in range(40):
            if not wait_for_edge_to(LOW, MAX_WAIT, f"bit {i} low before (ignore duration)"):  # Wait for the start of the bit (low), or on a loop iteration its already low by this time
                print(f"Timeout waiting for bit {i} low signal before high.")
                dump_data()
                return None
            # 50us

            if not wait_for_edge_to(HIGH, MAX_WAIT, f"bit {i} high"):  # Wait for the start of the bit (high)
                print(f"Timeout waiting for bit {i} high signal.")
                dump_data()
                return None
            high_start_time = time.time()

            if not wait_for_edge_to(LOW, MAX_WAIT, f"bit {i} low after"):  # Wait for the end of the bit (low)
                print(f"Timeout waiting for bit {i} low signal after high.")
                if i == 39:
                    # TODO generalize to recover from more missed bits, if we can assume they are first missed bits then IIAC I can recover up to 7 bits?
                    # YAY this is working well on sensor2 that was only working 20% of time before...!
                    # attempt to recover from first bit being missed
                    corrected_data = data.copy()
                    corrected_data.insert(0, 0)  # try zero first
                    if verify_sensor_data_checksum(bits_to_bytes(corrected_data)):
                        print("Recovered from missed first bit.")
                        return corrected_data
                    corrected_data = data.copy()
                    corrected_data.insert(0, 1)  # try one next
                    if verify_sensor_data_checksum(bits_to_bytes(corrected_data)):
                        print("Recovered from missed first bit.")
                        return corrected_data
                dump_data()
                return None
            high_duration = time.time() - high_start_time

            # AM2302 transmits a '0' if the high signal lasts around 26-28 µs,
            # and a '1' if it lasts around 70 µs
            if high_duration > 40 / 1_000_000:  # arbitrary => use 40us as threshold
                data.append(1)
            else:
                data.append(0)
            times.append(f"    bit {i} == {data[-1]}:   high duration => {high_duration * 1_000_000:.1f}us")

        print("Times:")
        for t in times:
            print("  ", t)
        return data


def bits_to_bytes(bits):
    bytes = []
    for byte_index in range(0, len(bits), 8):
        byte = 0
        for bit_index in range(8):
            byte = (byte << 1) | bits[byte_index + bit_index]
        bytes.append(byte)
    return bytes


def verify_sensor_data_checksum(bytes):
    humidity_high, humidity_low, temp_high, temp_low, checksum = bytes
    sum = humidity_high + humidity_low + temp_high + temp_low
    # last 8 bits of the sum of the first 4 bytes, IOTW ignore overflow beyond 8 bits
    calculated_checksum = sum & 0xFF
    print(f"Checksum: {checksum}, calculated: {calculated_checksum}, sum: {sum}")
    return calculated_checksum == checksum


def get_humidity(bytes):
    if len(bytes) < 2:
        return None
    # ANOTHER SPEC SHEET ... super detailed: https://files.seeedstudio.com/wiki/Grove-Temperature_and_Humidity_Sensor_Pro/res/AM2302-EN.pdf
    #
    # this guide says 16 bit precision: https://www.teachmemicro.com/how-dht22-sensor-works/
    # byte0 = humidity high byte, byte1 = humidity low byte
    humidity_high = bytes[0]
    humidity_low = bytes[1]
    humidity = humidity_high << 8 | humidity_low
    return humidity / 10.0  # reports in tenths


def get_temperature(bytes):
    if len(bytes) < 4:
        return None
    # byte2 = temperature high byte, byte3 = temperature low byte
    # BUT the first bit of byte2 is the sign bit
    sign = bytes[2] & 0b1000_0000
    temp_high = bytes[2] & 0b0111_1111
    temp_low = bytes[3]
    temperature = temp_high << 8 | temp_low
    temperature /= 10.0  # reports in tenths
    return temperature if not sign else -temperature


def read_am2302():
    send_start_signal_to_AM2302()

    bits = read_sensor_bits()
    print(f"bits: {bits}")

    if bits is None:
        print("Failed to read data from the sensor.")
        return None

    bytes = bits_to_bytes(bits)
    print(f"bytes: {bytes}")

    if not verify_sensor_data_checksum(bytes):
        print("Checksum verification failed.")
        return None

    return get_humidity(bytes), get_temperature(bytes)


result = read_am2302()

print()
if result:
    humidity, temperature = result
    print(f"Humidity: {humidity:.1f}%")
    print(f"Temperature: {temperature:.1f}°C, {temperature * 9 / 5 + 32:.1f}°F")
else:
    print("Failed to read sensor data.")
