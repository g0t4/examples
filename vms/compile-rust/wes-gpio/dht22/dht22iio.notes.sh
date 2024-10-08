## *** TODO try dtoverlay=dht22iio in /boot/firmware/config.txt + copy dtbo and ko to search paths

## *** NOTES MANUALLY LOADING overlay and module/driver...

# luck has it when I first tested this... I still had dht11 module loaded (from config.txt) so my dep just worked, but on reboot I found out that was an issue :)
# so I used:
sudo insmod dht22iio.ko # worked
dtc -@ -I dts -O dtb -o dht22iio-overlay.dtbo dht22iio-overlay.dts
sudo dtoverlay dht22iio-overlay.dtbo # worked
# and then I could see the device in /sys/bus/iio/devices/iio:device1
# b/c iio:device0 was dht11 driver
cat /sys/bus/iio/devices/iio:device1/in_temp_input # worked
cat /sys/bus/iio/devices/iio:device1/in_humidityrelative_input # worked

# then I removed dtoverlay=dht11,gpiopin=4 from /boot/firmware/config.txt
# and rebooted
# then I tried to insmod:
sudo insmod dht22iio.ko # failed
sudo dmesg # showed:
# [  346.103362] dht22iio: Unknown symbol __devm_iio_device_register (err -2)
# [  346.103387] dht22iio: Unknown symbol devm_iio_device_alloc (err -2)
# [  372.601004] dht22iio: Unknown symbol __devm_iio_device_register (err -2)
# [  372.601041] dht22iio: Unknown symbol devm_iio_device_alloc (err -2)
# [  438.954841] dht22iio: Unknown symbol __devm_iio_device_register (err -2)
# [  438.954871] dht22iio: Unknown symbol devm_iio_device_alloc (err -2)
#
# went out on a limb and tried to insmod dht11.ko
sudo insmod dht11.ko # worked
# then:
sudo insmod dht22iio.ko # worked this time!... so I have some dependency issue to resolve
#

# b/c of dependency issue:
sudo modinfo dht22iio.ko # see "depends: industrialio" ... so I need to load industrialio module first

# so here issue: I depend on industrialio module but its not loaded and when I use insmod it won't load it for me (unlike modprobe)
sudo modprobe industrialio # modprobe has search paths to load deps
sudo insmod dht22iio.ko # now, this works ... remember insmod literally just loads the module you pass, no search paths

## put in /boot/firmeware/config.txt:
# dtoverlay=dht22iio,gpio_pin=17
# dtoverlay=dht22iio,gpio_pin=27
#
# seems to ignore if overlay not found as I rebooted before `make install_driver`
#
# manual load before reboot:
sudo modprobe industrialio   # must load dep until I install_driver to modprobe mine
sudo insmod dht22iio.ko
sudo dtoverlay dht22iio.dtbo gpio_pin=17
cat /sys/bus/iio/devices/iio:device*/in_humidityrelative_input
# YASSSSSS!!!
sudo dtoverlay dht22iio.dtbo gpio_pin=27
# YAY both there ... # ! TODO now I need to address the timing issues... most of time one fails... a few times both responded
make install_driver
make status_driver
sudo reboot
# didn't work after first reboot... so I troubleshooted:
# FOUND dtoverlay had dht22iio (IIRC) so I moved on to troubleshoot dht22iio.ko (module/driver)
sudo modprobe dht22iio # failed... said not in /lib/modules... when it was... so I ran:
sudo depmod -a
sudo modprobe dht22iio # loaded! and /boot/firmware/config.txt overlays kicked in for both DHT22 sensors!!!!
ls /sys/bus/iio/devices/iio:device*/in_temp_input # w00h00
cat /sys/bus/iio/devices/iio:device0/in_temp_input # yay!
sudo reboot
# YAYAYAYA they are both there after reboot

# hwmon interface!
# hwmon loads an immediatley reads values from both channels...and it has retry logic b/c first channel failed and it read again... cool!
#
ls /sys/class/hwmon/
bat /sys/class/hwmon/*/name
# iio_hwmon@4  # ok that is where this node goes! lets give it a meaningful name then... I get it... second name is whatever I want so I can also override this if loading multiple, right?
#    RENAMED FYI to my own name dht22iio_hwmon@4 (and gpio_pin overrides the @4 too!)
cat /sys/class/hwmon/hwmon5/humidity1_input
cat /sys/class/hwmon/hwmon5/temp1_input
# yay! just a new set of file interfaces via the hwmon subsystem
