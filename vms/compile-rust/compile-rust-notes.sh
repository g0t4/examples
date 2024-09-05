
# bit more space
lsblk
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
df -h
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv

# clone linux-next
