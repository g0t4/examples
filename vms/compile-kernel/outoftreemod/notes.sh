make


sudo dmesg | tail
sudo insmod hello_mod.ko
sudo dmesg | tail

sudo rmmod hello_mod
sudo dmesg | tail

