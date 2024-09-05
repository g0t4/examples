
# bit more space
lsblk
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
df -h
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv

# clone linux-next
git clone https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git $HOME/linux-next

# override "ubuntu" default hostname
sudo hostnamectl set-hostname compile-rust



# host:
vagrant snapshot save linux-next


# kernel build deps:
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev

# setup initial config:
cd $HOME/linux-next
cp -v /boot/config-$(uname -r) .config
yes "" | make localmodconfig # strip down to local h/w modules/drivers... and answer default to questions
#
grep "SYSTEM_.*_KEYS" .config # check
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""
#
mkdir $HOME/configs
cp .config $HOME/configs/01-localmodconfig.config # for comparison later on


# check if LLVM is working:
make LLVM=1 menuconfig
# => clang: not found
# install llvm/clang:
sudo bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"
# validate:
llvm-config-18 --version
clang-18 --version
# NOTE might be newer version than 18, adjust accordingly

make LLVM=1 menuconfig # check again
# => still => clang: not found
make LLVM=-18 menuconfig # check again
#   => exit dont save changes
#   IIRC its recommended to use LLVM if building with rust support, gcc is experimental IIRC

make LLVM=-18 rustavailable
# => Rust compiler 'rustc' could not be found.
#   => fix issues one by one
# install rustup:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# proceed with standard installation
# exit shell / start new shell (b/c rustup is cached as not avail)
rustup --version # works
rustc --version # works
rustup show

make LLVM=-18 rustavailable
# => Rust bindings generator 'bindgen' could not be found.
cargo install --list # no bindgen-cli
cargo install --locked bindgen-cli
    cargo install --list # SHOWS!!!

make LLVM=-18 rustavailable
# => Source code for the 'core' standard library could not be found
rustup component add rust-src

make LLVM=-18 rustavailable
make rustavailable # FYI this can work too to test for rust support
make LLVM=1 rustavailable # However, this will report "unknown C compiler"

# now lets get config going and use the QR panic code as an example to test rust support
grep DRM_PANIC .config # "is not set"
#
# use menuconfig so I can show how w/o RUST=y then the QR code option doesn't show
make LLVM=-18 menuconfig
# Device Drivers => Graphics  support  => DRM => DRM_PANIC=y , DRM_PANIC_DEBUG=y
#    note no option for QR code (yet)
#    /QR_CODE => shows Depends on RUST [=n]
#    /RUST => depends on !MODVERSIONS
#    exit/save changes
scripts/config --disable CONFIG_MODVERSIONS
make LLVM=-18 menuconfig
# SHADOW_CALL_STACK s/b n (is y)
#   General Arch => disable shadow call stack # initial inspect looks ok to use:
#       scripts/config --disable SHADOW_CALL_STACK
#       I haven't yet tested that so leave it out
#  ok now, all the way up to:
#     "General setup" => "Rust support" => RUST=y
#  now up to:
#     "Device Drivers" => "Graphics support" => "DRM" => QR code = y
#         QR code option now shows
#  exit/save
#
grep DRM_PANIC .config # confirm
# one more option for base URL:
scripts/config --set-str CONFIG_DRM_PANIC_SCREEN_QR_CODE_URL "https://kdj0c.github.io/panic_report" # setting both on VM and build13
grep DRM_PANIC .config # show that one is changed
grep CONFIG_RUST .config
# s/b good to go!
cp .config $HOME/configs/03-rust-qr.config # for comparison later on

# FYI depend on env, if you have KVM loaded, you will need to disable -Werror for KVM (virutalziation => ...)
#
#
# alternative:
#    scripts/config --set-val CONFIG_DRM_PANIC_BACKGROUND_COLOR 0xff0000
    # ...

# compile it!
time make LLVM=-18 -j$(nproc)
# time w/ 4CPU and 4GB ram => 561.12 => 9.3s
# time w/ 10CPU and 16GB ram => 307s (WOW LLVM+rust is faster than gcc+no-rust)
# see below for LLVM w/o rust => 290.42s # not a big diff!

# at any time to restart and get accurate total compile time:
make clean mrproper
cp $HOME/configs/03-rust-qr.config .config

time sudo make modules_install # < 1s

time sudo make install
# fails b/c of parallel-tools (just remove these, NBD just lose shared volumes)
sudo dkms status # shows parallel-tools
sudo dkms remove -m parallels-tools -v 19.3.0.54924 --all # check version if failed
sudo dkms status # s/b none
sudo rm /boot/*6.11.0* # remove prev attempt(s)
time sudo make install # 3.5s

# check menu entries in grub:
sudo cat /boot/grub/grub.cfg | grep menuent
# don't need default or timeout changes if ok as is

# update grub to let me pick
cat /etc/default/grub
sudo sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=5/' /etc/default/grub
sudo sed -i 's/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/' /etc/default/grub
sudo sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT="1>0"/' /etc/default/grub
# black list vritio_gpu
sudo dmesg | grep drm # starts with simpledrm, blacklist subsequently loaded virtio_gpu
sudo sed -i 's/^GRUB_CMDLINE_LINUX=.*/GRUB_CMDLINE_LINUX="modprobe.blacklist=virtio_gpu"/' /etc/default/grub
sudo update-grub
sudo reboot

uname -a # w00t
# OPEN parallels GUI to see panic screen
echo 1 | sudo tee /sys/kernel/debug/dri/simple-framebuffer.0/drm_panic_plane_0
# qr code:
echo -n "qr_code" | sudo tee /sys/module/drm/parameters/panic_screen

# PROFIT! DONE!


# test LLVM w/o rust timing:
cp ../configs/03-rust-qr.config . # then will strip rust
make LLVM=-18 menuconfig
# General setup => Rust support = n
icdiff .config ../configs/03-rust-qr.config
# see how it updates depenedent config (ie QR_CODE=n now too)
cp .config $HOME/configs/04-llvm-no-rust.config
time make LLVM=-18 -j$(nproc) # 290.42s
