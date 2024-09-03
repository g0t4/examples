
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


# setup clang/llvm/rust/etc from notes about build13
make LLVM=-18 rustavailable # works (gonna use version in LLVM arg instead of aliasing clang to clang-18)
make LLVM=-18 menuconfig # saved
scripts/config --disable CONFIG_MODVERSIONS
# manually enable RUST (needed for DRM qr code option)
# manually enable DRM support + new panic screen options
# had to regen the .config b/c it was missing DRM support altogether?!
scripts/config --set-str CONFIG_DRM_PANIC_SCREEN_QR_CODE_URL "https://kdj0c.github.io/panic_report" # setting both on VM and build13
#   => confirmed in menuconfig too
scripts/config --set-val CONFIG_DRM_PANIC_BACKGROUND_COLOR 0x0000ff # blue bg
#
# confirms
grep DRM_PANIC .config
grep CONFIG_RUST .config
grep CONFIG_BINDGEN .config

# forgot certs
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""
# confirm
grep "CONFIG_SYSTEM_.*_KEYS" .config

# forgot to disable Virtualization => "Compile KVM with -Werror"
# scripts/config --disable CONFIG_KVM_WERROR # TODO verify this is the flag (it is not set after I manaully marked it in menuconfig)
#   resume compile
# FYI perhaps this is a culprit for the VM freeze last night... which btw I reverted to 6.8 kernel from ubuntu and so far have not had (KNOCK ON WOOD)
#     might be legit issues in KVM code in this linux-next src... wouldn't be surprising

# compile time!
make LLVM=-18 -j$(nproc)
sudo make LLVM=-18 modules_install
sudo make LLVM=-18 install
