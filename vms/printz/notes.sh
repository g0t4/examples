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

# !!! 2.0.0-0ubuntu10.1 # security patch release (automatic) applied on victim-vm ... I wanna roll back to 2.0.0-0ubuntu10 (s/b vulnerable)
#  *** YOU CAN SEE \" \" on quotes in the string... hrm... what might be overlooked still?
sudo apt remove -y cups
sudo apt autoremove -y
# *** https://launchpad.net/ubuntu/+source/cups-browsed/2.0.0-0ubuntu10.1  # OH WOW debian/patches/sec-202409-1.patch: disable legacy CUPS protocol in configure.ac.
# *** https://launchpad.net/ubuntu/+source/cups-browsed/2.0.0-0ubuntu10
# TODO pull both packages and diff them to see what all was fixed

# # lets disable security/updates
# cups:
#   Installed: (none)
#   Candidate: 2.4.7-1.2ubuntu7.3
#   Version table:
#      2.4.7-1.2ubuntu7.3 500
#         500 http://us.archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
#         500 http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages
#         100 /var/lib/dpkg/status
#      2.4.7-1.2ubuntu7 500
#         500 http://us.archive.ubuntu.com/ubuntu noble/main amd64 Packages

# *** TLDR I commented out security, noble-updates and noble-backports (didn't need to exclude backports but w/e)
sudo vim /etc/apt/sources.list.d/ubuntu.sources
# b/c the updates are on security and noble-updates
sudo apt update
# sudo apt install -y cups=2.4.7-1.2ubuntu7
sudo apt install -y cups # => selected cups=2.4.7-1.2ubuntu7  (GOOD SO FAR)
# *** I reset the config file too to pkg version... yup ok this most recent security release disabled CUPS remote browsing too (in addition to escaping \")
#
apt list --installed | grep cups
# cups-browsed/noble,now 2.0.0-0ubuntu10 amd64 [installed,automatic]
# cups-client/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# cups-common/noble,now 2.4.7-1.2ubuntu7 all [installed,automatic]
# cups-core-drivers/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# cups-daemon/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# cups-filters-core-drivers/noble,now 2.0.0-0ubuntu4 amd64 [installed,automatic]
# cups-filters/noble,now 2.0.0-0ubuntu4 amd64 [installed,automatic]
# cups-ipp-utils/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# cups-ppdc/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# cups-server-common/noble,now 2.4.7-1.2ubuntu7 all [installed,automatic]
# cups/noble,now 2.4.7-1.2ubuntu7 amd64 [installed]
# libcups2t64/noble,now 2.4.7-1.2ubuntu7 amd64 [installed,automatic]
# libcupsfilters2-common/noble,now 2.0.0-0ubuntu7 all [installed,automatic]
# libcupsfilters2t64/noble,now 2.0.0-0ubuntu7 amd64 [installed,automatic]

cups-browsed --version
# cups-browsed version 2.0.0
netstat -an | grep 631 # shows udp open still, makes sense
cat /etc/cups/cups-browsed.conf | grep BrowseRemoteProtocols
#   =>    BrowseRemoteProtocols dnssd cups

# try it out (fingers crossed for demo's sake on a new machine anyways)
sudo journalctl -u cups-browsed.service --follow
# WORKS !!!! YAY
# re-enable debug logging
sudo sed -i 's/^#.*DebugLogging stderr/DebugLogging stderr/' /etc/cups/cups-browsed.conf
sudo systemctl restart cups cups-browsed.service
sudo cat /etc/cups/ppd/192_168_122_1.ppd | grep -Pi "(foo|priv)"
#
# PRINT:
echo foo | lp -d 192_168_122_1
# YAY!!!

# ***! commands for forcing printer readded with IPPtoPPD redone
#
# monitor:
sudo journalctl -u cups-browsed.service --follow
lpstat -p  # -l
#
# (re)add printer:
  sudo systemctl restart cups cups-browsed
  sudo lpadmin -x 192_168_122_1
  #   => remove if restart alone isn't enough (i.e. after attempt printing)
  #
  # * restart/send UDP packet again
  #
  echo "foo" | lp -d 192_168_122_1
  #   => test print
  #
# verify ppd:
sudo cat /etc/cups/ppd/192_168_122_1.ppd | grep -Pi "(foo|priv)"
sudo cat /etc/cups/ppd/192_168_122_1.ppd
#      foomatic or privacy or whatever else

# disable unattented updates (then I can likely add back security if needed for other pkgs)
sudo systemctl stop unattended-upgrades.service
sudo systemctl disable unattended-upgrades.service