

# ok I wanna try build13 w/ QR code and see if it works
#    TRYING TO be a bit more careful and not just run commands rapidly
# AND extracted kernel src again too (entirely new src dir)

make LLVM=1 menuconfig    # fails b/c no clang (use as test to make sure I install it properly)
    bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"   # from https://apt.llvm.org/

    sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100
    sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-18 100
    sudo update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-18 100
    sudo update-alternatives --install /usr/bin/llvm-readelf llvm-readelf /usr/bin/llvm-readelf-18 100
    sudo update-alternatives --install /usr/bin/llvm-objcopy llvm-objcopy /usr/bin/llvm-objcopy-18 100
    sudo update-alternatives --install /usr/bin/llvm-nm llvm-nm /usr/bin/llvm-nm-18 100
    sudo update-alternatives --install /usr/bin/llvm-ar llvm-ar /usr/bin/llvm-ar-18 100
    sudo update-alternatives --install /usr/bin/llvm-strip llvm-strip /usr/bin/llvm-strip-18 100
    sudo update-alternatives --install /usr/bin/llvm-objdump llvm-objdump /usr/bin/llvm-objdump-18 100

    make LLVM=1 menuconfig # WORKS!

    # FYI copies current config and that is from panic screen kernel so these are already set correctly:
    cat .config   | grep DRM_PANIC
    # CONFIG_DRM_PANIC=y
    # CONFIG_DRM_PANIC_FOREGROUND_COLOR=0xffffff   # default already...
    # CONFIG_DRM_PANIC_BACKGROUND_COLOR=0x0000ff # red this time :)
    # CONFIG_DRM_PANIC_DEBUG=y
    # CONFIG_DRM_PANIC_SCREEN="user"

    # change => use red bg
    # sed -i 's/CONFIG_DRM_PANIC_BACKGROUND_COLOR=.*/CONFIG_DRM_PANIC_BACKGROUND_COLOR=0xff0000/' .config
    scripts/config --set-val CONFIG_DRM_PANIC_BACKGROUND_COLOR 0xff0000


# install rust
make LLVM=1 rustavailable  # fails, see message for help
# Rust compiler 'rustc' could not be found.

# QUICK START - RUST https://docs.kernel.org/rust/quick-start.html # linux docs for methods to install rust

    # install rustup: https://rustup.rs/
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    # Enter for standard install
    # output:
    #    To get started you may need to restart your current shell.
    #    This would reload your PATH environment variable to include
    #    Cargo's bin directory ($HOME/.cargo/bin).
    #
    #    To configure your current shell, you need to source
    #    the corresponding env file under $HOME/.cargo.
    #
    #    This is usually done by running one of the following (note the leading DOT):
    #    . "$HOME/.cargo/env"            # For sh/bash/zsh/ash/dash/pdksh
    #    source "$HOME/.cargo/env.fish"  # For fish
    #
    # FYI bashrc sources cargo env (was added in install)
    cat ~/.bashrc | grep cargo
    #    . "$HOME/.cargo/env"
    # exit and restart shell
    #
    rustc --version
    rustup --version
    rustup show # default is stable-x86_64-unknown-linux-gnu

    # rust bindings:
    make LLVM=1 rustavailable # FAILS => Rust bindings generator 'bindgen' could not be found.
    #
    # install via bindgen-cli
    cargo install --list # no bindgen-cli
    cargo install --locked bindgen-cli
        cargo install --list # SHOWS!!!

    make LLVM=1 rustavailable # FAILS => Source code for the 'core' standard library could not be found
    rustup component add rust-src # per quick start guide

    make LLVM=1 rustavailable # WORKS => Rust is available!

# configure RUST & QR CODE
make LLVM=1 menuconfig
# / RUST  => !MODVERSIONS must be off (it's yes currently)
# first time use scripts/config to modify config
    cp .config before.config # first time using scripts to modify config
    scripts/config --disable CONFIG_MODVERSIONS # ***
    icdiff before.config .config # confirmed just that one line is changed

# *** enable RUST support
# scripts/config --enable CONFIG_RUST # !!! does not do the same thing as menuconfig and manual selection?!
#
# MANUALLY SET IT:
    # lines modified in .config by menuconfig:
    # CONFIG_RUST_IS_AVAILABLE=y                                         # ADDED
    # CONFIG_RUST=y                                                      # ADDED
    # CONFIG_RUSTC_VERSION_TEXT="rustc 1.80.1 (3f5fd8dd4 2024-08-06)"    # ADDED
    # CONFIG_BINDGEN_VERSION_TEXT="bindgen 0.70.1"          # ADDED
    # CONFIG_ASM_MODVERSIONS=y                              # REMOVED
    # # CONFIG_RUST_FW_LOADER_ABSTRACTIONS is not set       # ADDED, commented out
    # # CONFIG_BLK_DEV_RUST_NULL is not set                 # ADDED, commented out
    # # CONFIG_RUST_PHYLIB_ABSTRACTIONS is not set          # ADDED, commented out
    # # CONFIG_DRM_PANIC_SCREEN_QR_CODE is not set          # ADDED, commented out
    # # CONFIG_SAMPLES_RUST is not set                      # ADDED, commented out
    # # CONFIG_RUST_DEBUG_ASSERTIONS is not set             # ADDED, commented out
    # CONFIG_RUST_OVERFLOW_CHECKS=y                         # ADDED
    # # CONFIG_RUST_BUILD_ASSERT_ALLOW is not set           # commented out

# *** MANUALLY set QR CODE, changes these lines:
# CONFIG_DRM_PANIC_SCREEN_QR_CODE=y       # this is the one I set in menuconfig, other two are set default too:
# CONFIG_DRM_PANIC_SCREEN_QR_CODE_URL=""
# CONFIG_DRM_PANIC_SCREEN_QR_VERSION=40

# backup
cp .config final.config

make LLVM=1 -j$(nproc)
# shit forgot this:
    # EXTRAVERSION = -qrcodewes
    # kill Ctrl+C make
    vim Makefile # set EXTRAVERSION = -qrcodewes
    make LLVM=1 clean
    make LLVM=1 menuconfig # save changes
        # updates commented out line that must be used to detect changes to EXTRAVERSION?
            # Linux/x86 6.11.0-rc5 Kernel Configuration  # BEFORE
            # Linux/x86 6.11.0-qrcodewes Kernel Configuration  # AFTER save menuconfig
        # no actual changes to .config (I confirmed) other than adding extraversion in commented out line
# FUCK accidentlaly rm * files fuck... oh well just re-extract kernel and all I Have to do is options
tar -xzf linux-next-next-20240830.tar.gz  # after installs diff version of tar is default...

# all options (as above)

make LLVM=1 -j$(nproc)
# error :(...
#   arch/x86/kvm/hyperv.c:2002:12: error: stack frame size (1336) exceeds limit (1024) in 'kvm_hv_flush_tlb' [-Werror,-Wframe-larger-than]
#   2002 | static u64 kvm_hv_flush_tlb(struct kvm_vcpu *vcpu, struct kvm_hv_hcall *hc)
#        |            ^
# WTF why is hyperv ...
#  disabling guest hyperv support (was marked =m so a module)
# Device Drivers => Microsoft hyperv guest => disable
# not doing a make clean, yet
# ... dont forget you are building on amd64 on tower, vs aarch64 on mac qemu VMs... that could explain speed diff in compile and also hyperv guest bug wasn't in VM
make LLVM=1 -j$(nproc)
# llvm build seems slower on my tower?! crazy...
#
# THOUGHTS waiting for compiles
#   FYI looking at the screen shots again for qr codes... makes me thing resolution could be the issue...
#       https://www.phoronix.com/news/Linux-6.12-DRM-Panic-QR-Code
#       => these are much bigger (comparing the logo in upper left vs the entire qr code so I wonder if there is not enough room in my VM display to show qr code and so it doesn't... there is logic looking at sizes of buffers before generating qr code...) => see https://www.phoronix.com/news/Linux-6.12-DRM-Panic-QR-Code
#           if so, I may not have a big enough monitor then (rpi monitor, unsure what its resolution is but its small too isn't it? perhaps hook up bigger external display - is that ninja 5 a 1080p display?)
#   ALSO, is it possible qr codes are working in amd64 but not aarch64 yet? another possible variable
#
# still had a fucking error on hyperv from maybe a diff module so I just...
#
# FUCKING KVM -Werror crap
#  I have seen this as a warning (frame buffer size) in other spots so just F it
#  menuconfig => Virtualization => disable Compile KVM with -Werror
#  resume building after this, shouldn't need to clean to resume
#    ok good =>   CC [M]  arch/x86/kvm/hyperv.o
#         BUT I THOUGHT I TURNED THIS OFF, I MUST NOT HAVE...

# asked chatgpt to read the qr code (copy/pasted it from  https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next/blob/985bf40edf4343dcb04c33f58b40b4a85c1776d4/drivers/gpu/drm/drm_panic.c )
# https://chatgpt.com/c/7fd36197-2567-41c7-8c91-134ffe4d1d4c
# it says yes the code will not show qr if display is too small... chatgpt estimated 420x730 needed at least... this has to be my issue...
#

# BTW
make LLVM=-18 ... # so I don't have to update alternatives

# ok red/white works so QR build is working on build13 but still not showing qr code... I suspect its cuz of screen size... lets try bigger screen
# fails on ninja with HDp60 HDMI input...
# checking size:
sudo apt install -y fbset
sudo fbset -s  # FYI VM gives same size as build13 here:
# mode "1024x768"
#    geometry 1024 768 1024 768 32
#    timings 0 0 0 0 0 0 0
#    rgba 8/16,8/8,8/0,0/0
# endmode
#
# FYI lots graphics info...
tree /sys/class/drm/card0
# i.e.:
cat card0-Unknown-1/modes
# 1024x768

sudo apt install -y libdrm-tests
sudo modetest -c
# FYI vm has 800x600 for simpledrm display :( ... so clearly neither work for qr code :(... nor can either be changed... what other drivers exist that support panic screen?

# OK I found some info on drivers:
# https://fedoraproject.org/wiki/Changes/EnableDrmPanic
#   *** nouveau is WIP so I should just wait for that if I think it's a screen size issue
#
#   FYI set viable web site to decode QR CODES: https://github.com/kdj0c/panic_report
scripts/config --set-str CONFIG_DRM_PANIC_SCREEN_QR_CODE_URL "https://kdj0c.github.io/panic_report" # setting both on VM and build13
#   *** test samples: https://github.com/kdj0c/panic_report/issues/1 => clearly these are high resolution displays, look how small tux is
#
#   OMG this describes everything I stumbled through, awesome:
#       https://fedoraproject.org/wiki/Changes/EnableDrmPanic#How_To_Test
#

# aside - fish shell
sudo apt install -y fish
sudo chsh -s /usr/bin/fish wes # don't need password this way

# FYI get rid of old builds in /boot
sudo rm /boot/*rc5-next*
sudo update-grub # unless gonna run `make LLVM=1 install` again and it will do this for you
# also FYI I forgot to add Makefile EXTRAVERSION on latest QR Code build so its just:
#   /boot/config-6.11.0-rc5-next-20240830
# make LLVM=1 modules_install / install

# set default to first item in adv sub menu
sudo sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT="1>0"/' /etc/default/grub
sudo update-grub

# drop time to change to 3 sec
sudo sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub

# INTERESTING!
# I switched to rpi 5" display and... the resolution defaults to 800x600 now!
#    but when I flipped cables before rebooting and it had the 1024x768 resolution (was on ninja v5 display and I moved cable to rpi 5" display)... the panic screen still shows but it was in a box with black borders all around so it was like it was using an even higher resolution...
#    HOW can I control the resolution? how is simpledrm negotiating a resolution? it obviously differs based on display as I suspected (ninja was higher)...
#
# can I find EDID data of the display and confirm that this is used  by simpledrm?
sudo apt install -y edid-decode read-edid
sudo get-edid | parse-edid # fails b/c no edid found
# crud edid is empty for my current simpledrm device
sudo cat /sys/class/drm/card0/card0-Unknown-1/edid # empty

# TODO try to force resolution
#   https://www.kernel.org/doc/html/latest/gpu/drm-kms.html#forcing-a-mode
#
#   Modify Kernel Parameters: You can pass kernel parameters to set the framebuffer resolution. For example:
#     video=HDMI-A-1:1024x768@60 video=DP-1:1920x1080@60
