
sudo apt update
sudo apt install -y kmscube
# kmscube failed, so I added these per chatgpt suggestion:
sudo apt install -y mesa-vulkan-drivers mesa-utils
sudo apt install -y mesa-va-drivers mesa-vdpau-drivers

kmscube # runs over SSH now... and renders frames (log output), no cube here b/c...
# VNC in to see the CUBE!!!! WORKS

ls /dev/dri # has dri devices too!


# *** spice grpahics fails:
virsh shutdown u2410
virsh define u2410 # spice graphics are not supported with this QEMU
# seems like my qemu build doesn't support spice graphics?!
