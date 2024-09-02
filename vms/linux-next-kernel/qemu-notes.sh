# see Vagrantfile for older notes
#
# set grub default to a specific kernel (0 based indexes into 1st menu and sub menus if applicable)
sudo sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT="1>2"/' /etc/default/grub
# 1 => is 2nd item which is "Advanced options for Ubuntu"
# 2 => is 3rd item which is "Ubuntu... qrcodewes..."
sudo update-grub
sudo reboot # watch on VNC => selects advanced menu entry and waits... at timeout it autoboots to the one I wantj
# FYI if default is a multi select 1>2 then if you hit enter while waiting it will select the submenu item too... so enter enter skips waiting
