import gpiod
import time

# Constants for GPIO and timing
AM2302_PIN = 17 # GPIO X pin
TIMEOUT_SEC = 2  # Timeout in seconds

# Timing constants (adjusted for Raspberry Pi)
MAX_WAIT = 0.1  # Maximum time to wait for signal in seconds
MIN_PULSE_WIDTH = 0.00005  # Minimum pulse width (50 µs)
HIGH_PULSE_THRESHOLD = 0.00007  # Threshold between 0 and 1 bit (70 µs)

# readability:
LOW = 0
HIGH = 1

chip = gpiod.Chip('gpiochip4')
line = chip.get_line(AM2302_PIN)

line.request(consumer='am2302-reader', type=gpiod.LINE_REQ_DIR_OUT)

def send_start_signal_to_AM2302():
    line.set_value(LOW)  # Pull the line low
    time.sleep(0.018)  # Wait for at least 18 ms
    line.set_value(HIGH)  # Release the line (high)
    time.sleep(0.00004)  # Wait for 40 µs (sensor will pull line low from 20 to 40 us later, wait max amount)
    # TODO add a check after 20 30 40us? so we don't wait too long?

def wait_for_edge_to(expected_value, timeout):
    """Wait for a change in the signal line to the expected value."""
    start_time = time.time()
    while line.get_value() != expected_value:
        if time.time() - start_time > timeout:
            return False
    return True

def read_sensor_data():
    data = []

    # Switch the line to input mode to read data from the sensor
    line.request(consumer='am2302-reader', type=gpiod.LINE_REQ_DIR_IN)

    # Wait for the sensor to pull the line low, then high (response signal)
    if not wait_for_edge_to(LOW, MAX_WAIT):
        print("Sensor didn't respond with a low signal.")
        return None

    if not wait_for_edge_to(HIGH, MAX_WAIT):
        print("Sensor didn't pull the line high.")
        return None

    # Sensor should now start sending 40 bits of data (5 bytes)
    for i in range(40):
        if not wait_for_edge_to(LOW, MAX_WAIT):  # Wait for the start of the bit (low)
            print(f"Timeout waiting for bit {i} low signal.")
            return None

        start_time = time.time()

        if not wait_for_edge_to(HIGH, MAX_WAIT):  # Wait for the high signal
            print(f"Timeout waiting for bit {i} high signal.")
            return None

        pulse_duration = time.time() - start_time

        # AM2302 transmits a '0' if the high signal lasts around 26-28 µs,
        # and a '1' if it lasts around 70 µs
        if pulse_duration > HIGH_PULSE_THRESHOLD:
            data.append(1)
        else:
            data.append(0)

    return data


def bits_to_bytes(bits):
    """Convert a list of bits to a list of bytes."""
    the_bytes = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        the_bytes.append(byte)
    return the_bytes


def verify_checksum(data):
    """Verify the checksum of the data received from the sensor."""
    humidity_high, humidity_low, temp_high, temp_low, checksum = data
    calculated_checksum = (humidity_high + humidity_low + temp_high + temp_low) & 0xFF
    return calculated_checksum == checksum


def read_am2302():
    send_start_signal_to_AM2302()

    raw_data = read_sensor_data()

    if raw_data is None:
        print("Failed to read data from the sensor.")
        return None

    # Convert the raw bits to bytes
    sensor_data = bits_to_bytes(raw_data)

    if not verify_checksum(sensor_data):
        print("Checksum verification failed.")
        return None

    # Convert the byte data to humidity and temperature values
    humidity = ((sensor_data[0] << 8) + sensor_data[1]) / 10.0
    temperature = ((sensor_data[2] << 8) + sensor_data[3]) / 10.0

    return humidity, temperature


# Read and display the data
result = read_am2302()

if result:
    humidity, temperature = result
    print(f"Humidity: {humidity:.1f}%")
    print(f"Temperature: {temperature:.1f}°C")
else:
    print("Failed to read sensor data.")

# Cleanup
chip.close()
