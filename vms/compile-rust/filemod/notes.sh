
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


