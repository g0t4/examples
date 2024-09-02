# see Vagrantfile for older notes
#
# set grub default to a specific kernel (0 based indexes into 1st menu and sub menus if applicable)
sudo sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT="1>2"/' /etc/default/grub
# 1 => is 2nd item which is "Advanced options for Ubuntu"
# 2 => is 3rd item which is "Ubuntu... qrcodewes..."
sudo update-grub
sudo reboot # watch on VNC => selects advanced menu entry and waits... at timeout it autoboots to the one I wantj
# FYI if default is a multi select 1>2 then if you hit enter while waiting it will select the submenu item too... so enter enter skips waiting


# TRYING force resolution
sudo vim /etc/default/grub
#    GRUB_CMDLINE_LINUX="video=simpledrm:1920x1080"

# BTW ssh
ssh -i github_ed25519  wes@localhost -p 2222

# OMG I just realized I might need to use a virtio monitor type and black list the driver so it uses simpledrm...
#   <model type='virtio' vram='65536' />
#   and I just started the VM and found:
#       grub initially showed really high resolution (def looked 1080p)
#       after grub passed, the screen stopped working (says "Display output is not active." right after that initial boot)
#          FYI... i see the same boot lines as when using ramfb... its just that ramfb keeps working to show panic screen
#
sudo dmesg | grep -i drm
sudo drm_info  # shows virtio_gpu for card2 (remember ever since switch to rust kernel there are three default drm cards and 2 is the one that goes to vnc)
#   now to blacklist:
#   GRUB_CMDLINE_LINUX="video=simpledrm:1920x1080 modprobe.blacklist=virtio_gpu"
#       *** still uses virtio_gpu (maybe modprobe'd?)
sudo update-grub
# sudo update-initramfs -u # didnt help to get blacklist to work...
#
# hrm
lspci -knn # shows driver by device
ls -al /sys/class/drm/card2/device  # confirm device # matches... so it is driver virtio-pci?!
#   *** says virtio-pci used?
# ASIDE =>  when looking for pci id to confirm in lspci... I found this
cat /sys/class/drm/card2/card2-Virtual-2/enabled # shows disabled on card 2 ... is that why it is turned off in vnc?
#  TODO can I re-enable it? wouldn't matter b/c virtio_gpu isn't compat w/ panic screen, AFAIK
#

# FYI in testing this old suggestion... this results in the card2 not even showing up in /sys/class/drm
# GRUB_CMDLINE_LINUX_DEFAULT="nomodeset simpledrm.modeset=1"
#
# I am stuck for now on getting model type="virtio" to work
#  <model type="vga" never shows the boot loader let alone anything else:
# FYI docs for types:  "vga", "cirrus", "vmvga", "xen", "vbox", "qxl" ( since 0.8.6 ), "virtio" ( since 1.3.0 ), "gop" ( since 3.2.0 ), "bochs" ( since 5.6.0 ), "ramfb" ( since 5.9.0 ), or "none" ( since 4.6.0 ), depending on the hypervisor features available.
#
