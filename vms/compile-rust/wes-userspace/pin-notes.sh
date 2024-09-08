
# IIUC some pins are pre-allocated on the RPI5 to a specific protocol and drivers 'listen' to these pins to detect a compatible device... so if I want to use the pins as general purpose GPIO I need to disable the driver that is listening to the pin?
lsmod | grep "i2c\|spi\|uart\|pwm" # TODO also pcm?, EEPROM?
# also would need to disable the driver in the device tree overlay
ls /boot/overlays/{i2c,spi,uart,pwm}*
# I2C1 is on pins 3,5
# UART is on pins 8,10
# SPI0 is on pins 19,21,23,24,26
# PWM0 is on pin 12
# PWM1 is on pin 33
# PCM 35, 38, 40
# EEPROM 27, 28

# FYI give perms to use gpio w/o sudo:
sudo usermod -aG gpio $USER

# FYI I stopped one of my flashing pins with one on...
sudo gpioget gpiochip4 17 27 22 # this returned 0 and reset all pins that were left on!
#  and I cannot run this when I am using the pins in python with gpiod library (request)
#
# gpioset works!
gpioget gpiochip4 17 27 22 # clears all to 0
gpioset gpiochip4 22=1 # turns on!
gpioset gpiochip4 27=1 # turns on!
gpioget gpiochip4 17 27 22 # resets too?!
gpioinfo # after gpioset the pin is marked "output"
#
gpioinfo # after gpioget the pin is marked "input"... so gpioget is changing direction to input
# TODO is there a way to read it w/o changing the direction?
# !!! makes sense actually if you wanna read the value then you are changing it to an input!