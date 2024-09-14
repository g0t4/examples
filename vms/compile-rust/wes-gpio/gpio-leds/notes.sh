## FYI found led controller that is a good resource:
# https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/leds/leds-gpio.c#L222

# TODO try this out
# also investigate it as a tool to use multiple devices with one driver

# list all overlays (not loaded, but discoverable)...
sudo dtoverlay -a | grep -i gpio
#
# w1-gpio # interesting
# https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/w1/masters/w1-gpio.c
