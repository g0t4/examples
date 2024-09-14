
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
sudo evtest /dev/input/event6 # then touch sensor => keys printed
# yay!