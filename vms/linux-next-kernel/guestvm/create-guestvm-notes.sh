# guestvm on build13 => see xml on that machine
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager ovmf -y

sudo kvm-ok  # good to go
# (thank god I didn't remove kvm in the custom kernel I built on the linux host when I was trying to get it to show panic QR lol...), I'll  be running my custom kernel as host kernel and  same custom kernel as guest kernel
sudo usermod -aG libvirt,kvm $USER
# logout/kill ssh sessions


# aside - my dotfiles for fish (on build13)..
git clone https://github.com/g0t4/dotfiles.git ~/repos/github/g0t4/dotfiles
ln --force -s ~/repos/github/g0t4/dotfiles/fish/config/config.fish ~/.config/fish/config.fish  # link to my fish config, logout/in to source
source ~/repos/github/g0t4/dotfiles/fish/install/install.fish # installs fisher + z
# PRN link other dotfiles like .grc and .gitconfig
sudo apt install -y silversearcher-ag
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | bash # or use iterm2 menu to do this
# iterm shell integration s/b to open remote files, todo try it
sudo apt install -y pipx # for osc-copy
pipx install oscclip # so I can copy to clipboard (i.e. ctrl+K to copy cmd line)
# => CRAP pipx failed to install (cannot find compat version)...
#     FUUUUU oscclip repo (https://github.com/rumpelsepp/oscclip?tab=readme-ov-file) marked archived as of Aug 2024 :(
#            did they pull oscclip?! YUP FUCK
#     suggests => https://github.com/theimpostor/osc
sudo apt install -y golang
go install -v github.com/theimpostor/osc@latest
#       update fish copy stuffs => "osc copy",   i.e. `echo foooooo | osc copy`


## back to guestvm.xml
virsh define guestvm.xml # works
# create disk
qemu-img create -f qcow2 ~/guestvm/disk1.qcow2 100G

# vm tweaking
# nvram will be taken from template into /var/lib/libvirt/qemu/nvram/guestvm_VARS.fd, saves cp template myself to that new location
#
sudo apt install -y net-tools
netstat -an | grep 5900 # I added graphics => vnc on 0.0.0.0 b/c that is easier to test for me
# tcp        0      0 0.0.0.0:5900            0.0.0.0:*               LISTEN # GOOD!
#
# OMG w00t w00t it works! (vnc => build13)... yes I know its not secured, I dont care about this guest
#
# TODO find spice interface...
#

# setup networking
#    https://libvirt.org/formatnetwork.html
# installer rightly shows no interfaces b/c I had none configured, unlike my mac where it got a nic OOB (with some sort of SLURP IIUC)
#
# NAT https://libvirt.org/formatnetwork.html#nat-based-network
#   PRN later can do bridged or otherwise so I can direct connect from network, though I dont need that for this project (panic screen)
virsh net-list --all  # obvi none
virsh net-define nat-default.xml
virsh net-start default
    # FAILED:
    #    error: Failed to start network default
    #    error: error creating bridge interface virbr0: Operation not permitted
sudo virsh net-start default # worked (I setup sudoless virsh but that isn't going to be all things it might do)
virsh net-autostart default # TODO does this work on reboot? or would it have permission issues?
# TODO network inactive state => crapola... hrm (sudo problems?)
# rebooting host to see if autostarts
#    => NOPE... not starting
sudo virsh net-start default # says started BUT still inactive
ip a # shows virbr0 and I can ping 192.168.122.1
# try to destroy it:
sudo virsh net-destroy default # works yes, and now virbr0 is gone
# OMG ..
virsh net-list # inactive
sudo virsh net-list # shows ACTIVE!
#       => *** also shows autostart no... do I need sudo for it to autostart?
# *** TODO remove autostart on lowely user?
#
# FUUUUUUU I was targeting the user session (b/c sudoless does that), thus why sudo shows diff domains/networks
virsh uri # => qemu:///session
virsh --connect qemu:///system net-list # => shows network
#
# CLEANUP qemu:///session (user session)
# destroys if needed, not in my case cuz I rebooted recently
virsh undefine guestvm --nvram
virsh net-undefine default

# specify system wide session:
export LIBVIRT_DEFAULT_URI=qemu:///system
virsh uri # validate => qemu:///system
#   ADDED to private fish.config (think per machine)
vim "$HOME/.config/fish/config-private.fish"
#   export LIBVIRT_DEFAULT_URI=qemu:///system
#
# now I can still do sudoless and target the system wide config
#    PART OF ME WONDERSS if it would be easier just to use sudo and have it default to system wide?
#
virsh net-autostart default
virsh define guestvm.xml

virsh define guestvm.xml
virsh start guestvm # FUUU permission denied
sudo systemctl status libvirtd.service # shows log failure too
#  Cannot access storage file '/home/wes/guestvm/disk1.qcow2' (as uid:..., gid:...):
# ok its running as libvirt-qemu

# lets move to standard location for libvirt, make new disk:
sudo mkdir -p /var/lib/libvirt/images
sudo mv ~/guestvm/disk1.qcow2 /var/lib/libvirt/images/
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/guestvm-primary.qcow2 100G
# FYI all images have SELinux basic confinement:
#    https://libvirt.org/drvqemu.html#selinux-basic-confinement
#    Also discussed:
#         https://superuser.com/questions/298426/kvm-image-failed-to-start-with-virsh-permission-denied
#
# I had nothing on the drive so just recreated and nuked
rm ~/guestvm/disk1.qcow2
#
# fix nvram path too and make its new dir:
/var/lib/libvirt/nvram
sudo mkdir -p /var/lib/libvirt/nvram
rm ~/guestvm/guestvm_VARS.fd # let it recreate it
#
# move ISO too  (ISOs are same thing as disks, so they must be protected too and cannot let system wide session be compromised so... I had to movee ISO to (even though it had read access for everyone from my home dir)
sudo mv ubuntu-24.04.1-live-server-amd64.iso  /var/lib/libvirt/boot/
#  ==> I chose /boot (could've used /images but IIUC boot meant for installer disks - or at least not same as images for drives)
# PRN try /isos? does that dir work for SELinux too?
sudo chown root:root /var/lib/libvirt/boot/ubuntu-24.04.1-live-server-amd64.iso
#
# OMFG finally it worked... ya know its permission denied errors should be a hell of a lot more clear about why they failed (mention SELinux or if its a blocked path or whatever just TELL ME)
virsh define guestvm.xml
virsh start guestvm # WORKED!!!!
# F YEAH installer working over VNC (and found the NIC!)
#   setup with same creds as my mac's qemu VM so the VMs are all the same for testing
#   I wish the auto partition would let me expand the /boot partition...  it is on 2GB too which is fine actually as i want most space for the drive to compile kernel and I can cleanup old kernels when I make install new ones




# ASIDE - FYI backup files on VM to this repo
scp "build13.lan:~/guestvm/*.xml" .


# guestvm OS installed and got access over VNC! yay, let's do spice now
sudo dmesg | grep drm # FYI starts with simpledrm then qxl (which is high res w/ spice IIUC)...
tree /sys/class/drm/ # shows card1 as pci...02.0 (matches guestvm.xml)
sudo apt install -y fbset edid-decode read-edid drm-info
sudo drm_info  # => yup qxl visible
cat /sys/class/drm/card1/card1-Virtual-1/modes # max is 1024 :( but does have other entries and this is VNC so it is possibly different otherwise, in fact
# TODO SPICE can't I set the resolution
# yes... Since 5.9.0, the model element may also have an optional resolution sub-element. The resolution element has attributes x and y to set the minimum resolution for the video device. This sub-element is valid for model types "vga", "qxl", "bochs", "gop", and "virtio".
# OMG resolution worked!!!! vnc is YUUUUGE.. so now I need to blacklist qxl driver
cat .../modes shows many more above previous top of 1024x768...  COOL
#  *** TODO - LEFT OFF HERE and see if I can get simpledrm to 1080p before I bother with copying over custom kernel and doing that via SSH


# TODO need SSH too, probably have to double hop to it so I can leave it NATd
#   TODO and IIUC I can map SSH to host port 2222 like on my mac... so I don't need to change network to expose default network to my network...
#      so like VNC/SPICE, SSH will be published to a host port so I don't need to route to my VM
#          THOUGH BE CAREFUL, VNC/SPICE are services run on host (not in guest), whereas SSH is a published port to the service running in my guest
# FYI ssh from build13 works IIUC w/o the port forward
sudo systemctl start ssh.service # was stoppped and disabled

ssh wes@192.168.122.180 # from build13 WORKS! good enough for me, screw the published port to the host


## OMG blacklist qxl driver worked... but I dont think the resolution is large?
#   GRUB_CMDLINE_LINUX_DEFAULT="video=simpledrm modprobe.blacklist=qxl"
#   drm_info shows simpledrm (can at least test panic screen though!)
sudo fbset -s # shows 1280x800! bigger by a smidge ... might enough w/o needing spice + simpledrm (if that even does anything different)

# scp'ing built kernel from host to guestvm
# WIP => installing build tools to be able to run make install  in VM which yikez means I need clang/rust/etc... NBD just do it when time permits
#    apt installs done for make
#    was in middle of notes-build13-qrcode's steps for clang and that is when VM froze FUUU... I wonder if my custom kernel is a bit brittle :)  and I should take host back to stable ubuntu 6.8
#         freezing happened one other time and `virsh destroy guestvm` DOES NOTHING (hangs then fails) => had to reboot last time
#
#
#   FALLBACK is to recompile entire kernel in the guestvm from scratch but I would like to avoid that
#     though I could do it overnight?!
#
#

GRUB_DEFAULT="1>4" # 5th entry, 6.8 original kernel should be more stable

# add entry to /etc/hosts
#    192.168.122.180 guestvm
#
# got guestvm configured for fish shell and other tools I like
sudo hostnamectl set-hostname guestvm
