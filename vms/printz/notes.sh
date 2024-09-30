# notes copying guestvm to victim (vm)

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
