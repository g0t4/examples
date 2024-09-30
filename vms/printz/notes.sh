# notes copying guestvm to victim (vm)
# shutdown guestvm and duplicate its disk (probably could do some sort of snapshotting and not need a full clone but meh for now, this way they are fully independent if I wanna nuke one and not both)

virsh define victim.xml
virsh start victim # -> took over guestvm dhcp lease (b/c was cached + client id same)
ssh victim # of course has same config so ssh all goood to go
sudo hostnamectl set-hostname victim

# regen machine id
sudo rm /etc/machine-id
sudo systemd-machine-id-setup
# restart
# dhcp should pick up a new lease
# confirm on host:
virsh net-dhcp-leases default

# install cups onto victim
# https://ubuntu.com/server/docs/install-and-configure-a-cups-print-server
sudo apt-get install -y cups
#  includes cups-browsed, cups-filters (with foomatic and my precious, foomatic-rip ;)
