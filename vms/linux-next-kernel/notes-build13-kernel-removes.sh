
# find kernel slugs:
ls /boot/config*

# /boot/config-6.8.0-45-generic  /boot/initrd.img-6.8.0-45-generic  /boot/System.map-6.8.0-45-generic  /boot/vmlinuz-6.8.0-45-generic

set uname_r "6.11.0-bluescreen-next-20240830"
set uname_r "6.11.0-rc5-next-20240830"

#! VERY CAREFUL with rm (i.e. not with empty uname_r var!)
if test -z "$uname_r"
    echo "uname_r is empty"
    return -1
end
echo foo
ls /boot/*$uname_r*
sudo --interactive rm /boot/*$uname_r*

# /lib/modules
ls /lib/modules/*$uname_r*
sudo rm -r /lib/modules/*$uname_r*

# review grub
sudo update-grub
sudo cat /boot/grub/grub.cfg | grep menuentry # make sure grub is configured for new kernel choices:
sudo vim /etc/default/grub # review DEFAULT choice
