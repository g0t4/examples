
# The Linux Kernel Module Programming Guide
#    Home: https://tldp.org/LDP/lkmpg/2.6/html/index.html
#

# 1.2 https://tldp.org/LDP/lkmpg/2.6/html/x44.html
lsmod
cat /proc/modules
# same output essentially, if strip header on lsmod:
diff_two_commands 'bat /proc/modules' 'lsmod | tail -n +2' 

# finding the module
cat /etc/modprobe.conf
# blacklisting modules:
cat /etc/modprobe.d/blacklist*.conf
cat /etc/modprobe.d/dkms.conf # DKMS
#
# show effective config (of /etc/modprobe.d/*.conf et al)
modprobe -c


make LLVM=-18 # compile modules w/ same compiler and version used to compile kernel (in my rust env I am using LLVM tooling v18)
modinfo filemod.ko # shows metadata from module source file
modinfo hid # find module and show its info, hid is in:
sudo ls  /lib/modules/$(uname -r)/ # IIUC from make modules_install (kernel modules)
# FYI modinfo shows:
# intree:
# depends:
# filename:

# load hello world module (filemod)
insmod filemod.ko
lsmod | grep filemod
sudo dmesg | tail -n 1
rmmod filemod
sudo dmesg | tail -n 1

