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

# PRN address these warnings? BTW dht11-overlay.dts has same warnings so for now I am gonna skip this unless I have an issue that necessitates addressing this...
#
dtc -O dtb -o touch-sensor-unified.dtbo touch-sensor-unified.dts
# touch-sensor-unified.dts:10.58-14.15: Warning (unit_address_vs_reg): /fragment@0/__overlay__/touch_sensor_unified@4: node has a unit name, but no reg or ranges property
#
dtc -I fs /proc/device-tree 2>&1 | grep touch_sensor
# <stdout>: Warning (unit_address_vs_reg): /touch_sensor_unified@1a: node has a unit name, but no reg or ranges property
# <stdout>: Warning (unit_address_vs_reg): /touch_sensor_unified@10: node has a unit name, but no reg or ranges property
# <stdout>: Warning (gpios_property): /touch_sensor_unified@1a:gpios: cell 0 is not a phandle reference
# <stdout>: Warning (gpios_property): /touch_sensor_unified@10:gpios: cell 0 is not a phandle reference


## FYI testing dtoverlay in /boot/firmware/config.txt
sudo vim /boot/firmware/config.txt
# # enable dht11:
# dtoverlay=dht11,gpiopin=17
# dtoverlay=dht11,gpiopin=27
bat --style=header /sys/bus/iio/devices/iio:device*/in_*_input

# ok b/c of two boot partititons... if /boot/firmware => nvme0n1p1 (still before that was mmcblk0p1 b/c it is picking up my dtoverlay's... its like it remounts to nvme0n1p1 sometimes and must be after mmcp1 b/c my config.txt from mmc is still used)
sudo mkdir -p /mount/mmc-boot
sudo mount /dev/mmcblk0p1 /mount/mmc-boot/
sudo vim /mount/mmc-boot/config.txt # odd in this case its not firmware/config.txt ... what is this odd behavior...
# TODO fix booting off one predictable spot... preferrably not the SD card (maybe remove sd card to be sure, does nvme boot alone)

# copy overlay and driver to be discoverable on boot
# ls "/lib/modules/$(uname -r)/kernel/drivers/iio/humidity" # dht11.ko.xz here
#
# foo tried to add modules_install to Makefile and ended up wiping out: /lib/modules/6.6.31+rpt-rpi-2712/build
dpkg -S /lib/modules/6.6.31+rpt-rpi-2712/build
sudo apt install  --reinstall linux-headers-6.6.31+rpt-rpi-2712 # PHEW this put back /build!
# kernel/ dir gone too
dpkg -S /lib/modules/6.6.31+rpt-rpi-2712/kernel
# linux-image-6.6.31+rpt-rpi-2712: /lib/modules/6.6.31+rpt-rpi-2712/kernel
sudo apt install --reinstall linux-image-6.6.31+rpt-rpi-2712  # put kernel/ back

# gonna put mine with humidity sensors (i.e. next to dht11)
sudo cp touch.ko /lib/modules/$(uname -r)/kernel/drivers/iio/humidity/
