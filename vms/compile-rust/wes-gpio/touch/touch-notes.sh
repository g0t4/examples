
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
