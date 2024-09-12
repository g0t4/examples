
# research loading DHT11.dto overlay to use DHT22 instead of my kernel driver.. this will help me setup the device tree overlay for my driver

# found dht11.c in kernel source code
#   https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/iio/humidity/dht11.c#L265
ag -g dht11 ~/rpi-linux/
# /home/pi/rpi-linux/drivers/iio/humidity/dht11.c
# /home/pi/rpi-linux/arch/arm/boot/dts/overlays/dht11-overlay.dts
#     see uses pin 4 by default: https://github.com/raspberrypi/linux/blob/rpi-6.8.y/arch/arm64/boot/dts/overlays/dht11-overlay.dts#L32-L38
#     TODO IIGC I can use gpiopin to override pin? in config.txt?
# /home/pi/rpi-linux/Documentation/devicetree/bindings/iio/humidity/dht11.yaml
#
# compiled overlay:
ag -g dht11 /boot
#   /boot/firmware/overlays/dht11.dtbo
#
# can also decompile overlay if not find source
dtc -I dtb -O dts -o overlay.dts /boot/firmware/overlays/dht11.dtbo


# enable overlay:
sudo vim /boot/firmware/config.txt
# add:
#     dtoverlay=dht11  
reboot
lsmod | grep dht11 # to see if it is loaded (assuming connected to pin 4)

ls /sys/bus/iio/devices/iio:device0 # YAY!
cat /sys/bus/iio/devices/iio:device0/in_temp_input # remember this is 1000*temp
cat /sys/bus/iio/devices/iio:device0/in_humidityrelative_input # remember this is 1000*humidity %

# NEXT UP TEST boot w/o it connected to pin 4
# ok so it still loads module
sudo lsmod | grep dht11 # still shows
sudo dmesg # no failures yet
cat /sys/bus/iio/devices/iio:device0/in_humidityrelative_input # hangs and then returns nothing after timeout in dht11 driver
sudo dmesg # shows:
# [   69.182357] dht11 dht11@4: Only 0 signal edges detected
# really this is the only way to handle the issue as there is no way to tell if the chip is actually present or not short of asking it for temp/humidity... so the probe method can't return a failure like I bet it could with other buses


# NEXT UP try to use pin 17
sudo vim /boot/firmware/config.txt
# add: # wtf my config.txt didn't have dtoverlay=dht11 in it? AFTER REBOOT it is removed?!
#     dtoverlay=dht11,gpiopin=17
#   failed to work :(... switched back to pin 4 and that one works (live switch w/o reboot)