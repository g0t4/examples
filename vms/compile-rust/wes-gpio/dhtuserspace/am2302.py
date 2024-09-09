import gpiod
import time
from gpiod.line import Direction, Value

TIMEOUT_SEC = 2  # Timeout in seconds
MAX_WAIT = 0.1  # Maximum time to wait for signal in seconds

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
        request.set_value(LINE, LOW)  # TODO do I need this if I already set output low in the config above?
        time.sleep(0.018)  # Wait for at least 18 ms
        request.set_value(LINE, HIGH)
        time.sleep(20 / 1_000_000)  # keep high for 20-40us


def read_sensor_bits():
    data = []
    times = []

    # Switch the line to input mode to read data from the sensor
    with gpiod.request_lines("/dev/gpiochip4", consumer="dht22-input", config={LINE: gpiod.LineSettings(direction=Direction.INPUT)}) as request:

        def wait_for_edge_to(expected_value: Value, timeout):
            """Wait for a change in the signal line to the expected value."""
            start_time = time.time()
            while request.get_value(LINE) != expected_value:
                if time.time() - start_time > timeout:
                    return False
            total_us = (time.time() - start_time) * 1_000_000
            times.append(f"{total_us:.1f} => {expected_value}")
            return True

        def dump_data():
            print(f"data: {data}")

            num_complete_bits = len(data) // 8
            complete_bits = data[:num_complete_bits * 8]
            complete_bytes = bits_to_bytes(complete_bits)
            print(f"Data so far: {complete_bytes}")

            humidity = get_humidity(complete_bytes)
            temperature = get_temperature(complete_bytes)
            print(f"Humidity: {humidity:.1f}%, Temperature: {temperature:.1f}°C")

            print("Times:")
            for t in times:
                print(t)

        # Wait for the sensor to pull the line low, then high (response signal)
        if not wait_for_edge_to(LOW, MAX_WAIT):
            # ~80us
            print("Sensor didn't respond with a low signal.")
            return None
        # 80us low

        if not wait_for_edge_to(HIGH, MAX_WAIT):
            print("Sensor didn't pull the line high.")
            return None
        # 80us high

        # Sensor should now start sending 40 bits of data (5 bytes)
        for i in range(40):
            if not wait_for_edge_to(LOW, MAX_WAIT):  # Wait for the start of the bit (low), or on a loop iteration its already low by this time
                print(f"Timeout waiting for bit {i} low signal before high.")
                dump_data()
                return None
            # 50us

            if not wait_for_edge_to(HIGH, MAX_WAIT):  # Wait for the high signal
                print(f"Timeout waiting for bit {i} high signal.")
                dump_data()
                return None
            high_start_time = time.time()

            if not wait_for_edge_to(LOW, MAX_WAIT):  # Wait for the end of the bit (low)
                print(f"Timeout waiting for bit {i} low signal after high.")
                dump_data()
                return None
            high_duration = time.time() - high_start_time

            # AM2302 transmits a '0' if the high signal lasts around 26-28 µs,
            # and a '1' if it lasts around 70 µs
            if high_duration > 40 / 1_000_000:  # arbitrary => use 40us as threshold
                data.append(1)
            else:
                data.append(0)

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
    return ((bytes[0] << 8) + bytes[1]) / 10.0


def get_temperature(bytes):
    if len(bytes) < 4:
        return None
    return ((bytes[2] << 8) + bytes[3]) / 10.0


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

if result:
    humidity, temperature = result
    print(f"Humidity: {humidity:.1f}%")
    print(f"Temperature: {temperature:.1f}°C")
else:
    print("Failed to read sensor data.")
