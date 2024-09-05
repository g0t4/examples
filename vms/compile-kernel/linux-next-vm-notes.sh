# timing done on (my m1 mac w/ 10 cores and 8GB ram for the parallels VM)
vagrant init wesdemos/ubuntu2410-arm
vagrant up

# setup direct ssh access to VM
vagrant ssh-config --host compile-kernel  > ~/.ssh/config.d/vagrant-compile-kernel
trash ~/.ssh/config.d/vagrant-compile-kernel


# *** generate config
# route A
# start with current config
cp -v /boot/config-$(uname -r) .config
# strip down (should compile faster b/c only will run on current arch + modules)
yes "" | make localmodconfig # yes "" => answer with default on all questions
#
# OR route B
cp -v /boot/config-$(uname -r) .config
make olddefconfig # answer with default on all new questions
make localmodconfig

### *** overrides
grep "SYSTEM_.*_KEYS" .config # check
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""


# *** compile
time make -j$(nproc) # 342.74 secs, 331s round2

# *** TODO repeat compile tests with LLVM/clang


# make modules_install
time sudo make modules_install # 1 second, 1s round2

time sudo make install # FAILS:
# b/c dkms + parallels-tools
sudo dkms status # shows parallel-tools
sudo dkms remove -m parallels-tools -v 19.4.0.54962 --all
time sudo make install # 2.51 seconds, 3s round2

# FYI remove old kernel installs:
sudo rm /boot/*6.11.0*
sudo update-grub # find order of kernels based on detected output, OR:
sudo cat /boot/grub/grub.cfg | grep menuent   # dump menu entries in generated grub.cfg

# set default kernel
bat /etc/default/grub
# 1 == advanced, 2 == 3rd item (menu entry in the advanced menu)
#  DO NOT LEAVE OFF "" quotes, that was failing for me
sudo sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT="1>2"/' /etc/default/grub
    sudo update-grub

# 5 sec timeout grub:
sudo sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=5/' /etc/default/grub
    sudo update-grub
# show grub menu:
sudo sed -i 's/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/' /etc/default/grub
    sudo update-grub


#
# cp backup config before mrproper:
make clean
make mrproper
# cp .config back same as before
# crap llvm isn't supported on 24.10 currently... so come back to this later

# *** (round2) lets retime gcc after clean/mrproper

# *** (round3) test speed to recompile w/ panic screen (after full compile worked)

grep DRM_PANIC .config
scripts/config --enable DRM_PANIC
scripts/config --enable DRM_PANIC_DEBUG
make olddefconfig # set defaults on other DRM_PANIC options:
# CONFIG_DRM_PANIC=y                                                                           # CONFIG_DRM_PANIC is not set
# CONFIG_DRM_PANIC_FOREGROUND_COLOR=0xffffff
# CONFIG_DRM_PANIC_BACKGROUND_COLOR=0x000000
# CONFIG_DRM_PANIC_DEBUG=y
# CONFIG_DRM_PANIC_SCREEN="user"
cp .config ../configs/02-gcc-w-drm-panic.config
time make -j$(nproc) # round3: 36s
sudo rm /boot/*6.11.0*
time sudo make modules_install # round3: 1s
time sudo make install # round3: 3s

# todo blacklist gpu drivers (uses simpledrm before virtio_gpu)
# GRUB_CMDLINE_LINUX="video=simpledrm "
sudo sed -i 's/^GRUB_CMDLINE_LINUX=.*/GRUB_CMDLINE_LINUX="modprobe.blacklist=virtio_gpu"/' /etc/default/grub
    sudo update-grub
sudo reboot
#
sudo apt install -y fbset edid-decode read-edid drm-info
# double check simpledrm after blacklist
sudo fbset -s # ensure simpledrm at top of output OR if multi device somewhere in output
sudo ls /sys/kernel/debug/dri/simple-framebuffer.0/drm_panic_plane_0
sudo ls /sys/module/drm/parameters/panic_screen # config for type of panic screen

# logo higher quality (mono)
scripts/config --enable CONFIG_LOGO
scripts/config --enable CONFIG_LOGO_LINUX_MONO
# then the panic screen uses the mono logo (not ascii logo)
#
# FYI there are other logics (color) but the panic module calls fb_find_logo(1) which sets color depth to 1 (mono) as max:
#   https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next/blob/985bf40edf4343dcb04c33f58b40b4a85c1776d4/drivers/gpu/drm/drm_panic.c#L42
#
scripts/config --set-val CONFIG_DRM_PANIC_BACKGROUND_COLOR 0xff00df # pink
scripts/config --set-val CONFIG_DRM_PANIC_FOREGROUND_COLOR 0x000000 # white
# FYI --set-str wraps the value in quotes, --set-val does not
grep DRM_PANIC .config

# disable blinking cursor on login screen:
sudo sed -i 's/^GRUB_CMDLINE_LINUX=.*/GRUB_CMDLINE_LINUX="modprobe.blacklist=virtio_gpu vt.global_cursor_default=0"/' /etc/default/grub
    sudo update-grub

# trigger panic w/o sudo so
echo 1 | sudo tee /sys/kernel/debug/dri/simple-framebuffer.0/drm_panic_plane_0

# FYI kernel code to register panic handler AND debugfs handler:
#   https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next/blob/985bf40edf4343dcb04c33f58b40b4a85c1776d4/drivers/gpu/drm/drm_panic.c#L1021
#   thus, we can trigger panic display w/o a real panic using debugfs b/c it has a separate registration that doesn't have to get monkey patched through a real panic
#
# here is what looks like logic to decide which drm devices are supported:
#    https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next/blob/985bf40edf4343dcb04c33f58b40b4a85c1776d4/drivers/gpu/drm/drm_panic.c#L994
#    IIGC this would be what limits to simpledrm (etc)? indirectly via what is available in the driver plane?
