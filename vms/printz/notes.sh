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

# TODO try:
cupsctl --debug-logging
# etc

# *** get victim VM configured for demo
cups-browsed --version # 2.0.0 vs host1 demo env was 1.28
# victim did not have 631/udp open, from testing b/c cups protocol was not enabled in remote protocols list (IIUC cups is being phassed out? in favor of dnssd and ippeverywhere?)
# *** cups-browsed.conf:  (controls 631/udp)
#   BrowseRemoteProtocols dnssd cups # was just dnssd (added cups) # ***! this opened 631/udp
#   FYI BrowseLocalProtocols/BrowseProtocols (both) could be used too
sudo systemctl restart cups cups-browsed.service
#
sudo netstat -anp | grep 631 # FYI! do not forget sudo, else won't see executable name/pid
sudo ss -anp | grep 631
# *** cupsd.conf:  (controls 631/tcp) - No chanegs so far
#   Browsing No # PRN set "Yes"? (IIGC this is for sharing printers back out to other CUPs servers and clients?) I just wanna register printers to this machine so probably not gonna need this ever
#   Listen localhost:631 # ? both hosts have localhost:631 for cupsd
#
# FYI compare cups configs:
diff_two_commands 'ssh host1 -C "cat /etc/cups/cupsd.conf"' 'ssh victim -C "cat /etc/cups/cupsd.conf"'
diff_two_commands 'ssh host1 -C "cat /etc/cups/cups-browsed.conf"' 'ssh victim -C "cat /etc/cups/cups-browsed.conf"'
#

# rework the simplest possible server.py to demo this => yay got a response from UDP packet!
veinit # ...
python3 servers/server1.py

