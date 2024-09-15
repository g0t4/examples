from sense_hat import SenseHat

sense = SenseHat()

with open("/sys/bus/iio/devices/iio:device0/name") as f:
    print(f"DHT22: {f.read().strip()}")

with open("/sys/bus/iio/devices/iio:device0/in_temp_input") as f:
    temp = float(f.read()) / 10
    print(f"  Temperature: {temp}C")

with open("/sys/bus/iio/devices/iio:device0/in_humidityrelative_input") as f:
    humidity = float(f.read()) / 10
    print(f"  Humidity: {humidity}%")
print()

fahrenheit = 9 / 5 * sense.get_temperature() + 32

print("SenseHat:")
print(f"  Temperature: {sense.get_temperature():.1f}C ({fahrenheit:.1f}F)")
print(f"  Humidity: {sense.get_humidity():.1f}%")
print(f"  Acceleration: {sense.accelerometer_raw}")
print()

sense.set_rotation(180)
sense.clear()
temp_str = f"{temp:.1f}C"
sense.show_message(temp_str, text_colour=[0, 255, 0])
