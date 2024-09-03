# guestvm on build13 => see xml on that machine
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager ovmf -y

sudo kvm-ok  # good to go
# (thank god I didn't remove kvm in the custom kernel I built on the linux host when I was trying to get it to show panic QR lol...), I'll  be running my custom kernel as host kernel and  same custom kernel as guest kernel
sudo usermod -aG libvirt,kvm $USER
# logout/kill ssh sessions


# aside - my dotfiles for fish..
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
# network inactive state, IIAC b/c no interfaces (domains) attached?

# FYI backup files on VM to this repo
scp "build13.lan:~/guestvm/*.xml" .

# redefine virsh VM
