
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

