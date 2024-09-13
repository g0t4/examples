# https://www.raspberrypi.com/products/sense-hat/
# https://pythonhosted.org/sense-hat/
from sense_hat import SenseHat

sense = SenseHat()

# pins used by sensehat:
# https://pinout.xyz/pinout/sense_hat


# i2c group required:
fahrenheit = 9 / 5 * sense.get_temperature() + 32

print(f"Temperature: {sense.get_temperature():.1f}C ({fahrenheit:.1f}F)")
print(f"Humidity: {sense.get_humidity():.1f}%")
print(f"Acceleration: {sense.accelerometer_raw}")

# input and video groups required:
sense.set_rotation(180)
sense.clear()
sense.show_message("zed!", text_colour=[0,255,0])





# groups for permissions:
# sudo python3  demo.py
# must run as root (current permissions), or if not root:
#   in .venv => ModuleNotFoundError: No module named 'RTIMU'
#   in $HOME dir => Permission denied: '/dev/input/event5)
#     ls -l /dev/input/event5 # root:input (owner:group)... can I add myself to input group to not need sudo?
#     sudo usermod -aG input $USER
#   => next =>
#     Permission denied: '/dev/fb0'
#     sudo usermod -aG video $USER
#     PROFIT!!!!
#        ASIDE:    sudo dmesg | grep fb0  =>  fb0: RPi-Sense FB frame buffer device
# "i2c" group for temp/humidity
# "spi" => for "Atmel chip can be reprogrammed via the SPI interface" (IIAC not configured out of box for this)
