
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

# find pkg
apt-file search $(which modprobe)
# kmod: /usr/sbin/modprobe
dpkg -L kmod
# /bin/kmod
# ...
# /bin/lsmod
# /sbin/depmod
# /sbin/insmod
# /sbin/lsmod
# /sbin/modinfo
# /sbin/modprobe
# /sbin/rmmod
kmod --list
ls -al /sbin/*mod
# lrwxrwxrwx 1 root root      9 Nov 30  2023 /sbin/depmod -> /bin/kmod*
# ...
# lrwxrwxrwx 1 root root      9 Nov 30  2023 /sbin/insmod -> /bin/kmod*
# lrwxrwxrwx 1 root root      9 Nov 30  2023 /sbin/lsmod -> /bin/kmod*
# lrwxrwxrwx 1 root root      9 Nov 30  2023 /sbin/rmmod -> /bin/kmod*
# so, dep/ins/ls/rmmod are all symlinks to kmod, an old school subcommand mechanism

# can't load a module for a diff kernel version UNLESS you set CONFIG_MODVERSIONS=y in the kernel config (and rust support requires disabling MODVERSIONS)

# FYI useful to compile fresh, stock kernel so you have all headers for compiling your modules

# filemod change to use KERN_WARNING macro
sudo dmesg --level warn  # LEVELS: info, notice, warn, err, crit, alert, emerg, debug
sudo dmesg --json # includes "pri" (level)
sudo dmesg --raw # includes "pri" on front
# <6>[ 2370.069896] Goodbye, world!
sudo dmesg --human/-h # when batches of messages (based on time) are shown, first in a batch shows full time, then rest show delta from first
# [Sep 7 14:32] filemod: module license 'MIT' taints kernel.
# [  +0.000005] Disabling lock debugging due to kernel taint
# [  +0.000000] filemod: module license taints kernel.
# [  +0.001324] Hello, world!
# [ +40.214101] Goodbye, world!
# [Sep 7 14:33] Hello, world!
# *** FYI, this doesn't mean they are related, just that they arrived about the same time as others


# quickly reload and see printk output
sudo rmmod filemod; sudo insmod filemod.ko; sudo dmesg --raw | tail

