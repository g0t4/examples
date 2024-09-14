# testing:
make
sudo dmesg --clear
sudo dtoverlay touch-sensor.dtbo
sudo  ls /dev/input/event* # were 5 events
sudo insmod touch.ko
sudo dmesg # w00h00

sudo ls -al /dev/input/event* # now event6!
# note group is "input" and I already have that on my "pi" user so no need for sudo

cat /dev/input/event6 # then touch sensor => keys printed

sudo apt install evtest -y
evtest # lists devices, ctrl+c to exit

evtest /dev/input/event6 # then touch sensor => keys printed:
#
# Input driver version is 1.0.1
# Input device ID: bus 0x0 vendor 0x0 product 0x0 version 0x0
# Input device name: "touch_sensor"
# Supported events:
#   Event type 0 (EV_SYN)
#   Event type 1 (EV_KEY)
#     Event code 28 (KEY_ENTER)
# Properties:
# Testing ... (interrupt to exit)
#
# Event: time 1726273933.816870, type 1 (EV_KEY), code 28 (KEY_ENTER), value 0
# Event: time 1726273933.816870, -------------- SYN_REPORT ------------
# Event: time 1726273934.107229, type 1 (EV_KEY), code 28 (KEY_ENTER), value 1
# Event: time 1726273934.107229, -------------- SYN_REPORT ------------
#
# FYI those 4 lines are from one press/release of the touch sensor

# BTW use by-path for paths that don't change
evtest /dev/input/by-path/platform-touch_sensor_16-event
evtest /dev/input/by-path/platform-touch_sensor_26-event
# that way when input device is removed then the /dev/input/event* number changes don't mess up which one you are working with...
# also don't `dtoverlay -r touch_sensor_26` when you are `evtest ...` on it :).. that might have caused ssh instability I randomly had

# ** OMG... unified dht11 might be working after I added "reg:0" to be updated too (the node@address)
sudo dtoverlay touch-sensor-unified.dtbo gpio_pin=26
ls /dev/input/by-path/*unified*
# platform-touch_sensor_unified@1a-event    # YAY has 0x1a == 26
evtest /dev/input/by-path/platform-touch_sensor_unified@1a-event # works!
#
sudo dtoverlay touch-sensor-unified.dtbo  gpio_pin=16
# sudo dmesg # loaded, no errors!!!
ls /dev/input/by-path/*unified*
# also has: # platform-touch_sensor_unified@10-event # YAY
evtest /dev/input/by-path/platform-touch_sensor_unified@10-event # works!
# F YES! it worked... I knew chatgpt was just wrong when said cannot do this repeatedly in several threads last night...

sudo dtoverlay -l
# Overlays (in load order):
# 0:  dht11  gpiopin=17
# 1:  dht11  gpiopin=27
# 2:  touch-sensor-unified  gpio_pin=26
# 3:  touch-sensor-unified  gpio_pin=16

# look at docs to confirm reg override...
# https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/configuration/device-tree.adoc
#
# When assigning to the reg property, the address portion of the parent node name will be replaced with the assigned value.
# This can be used to prevent a node name clash when using the same overlay multiple times - a technique used by the i2c-gpio overlay.
#
# TLDR overriding "reg:0" also replaces the node@address
#
# "reg" is also a separate property that can be set on the node, like a bus 



