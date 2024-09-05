# timing done on (my m1 mac w/ 10 cores and 8GB ram for the parallels VM)
vagrant init wesdemos/ubuntu2410-arm
vagrant up


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
time make -j$(nproc) # 342.74 secs

# *** TODO repeat compile tests with LLVM/clang


# make modules_install
time sudo make modules_install # 1 second!

time sudo make install # FAILS:
# b/c dkms + parallels-tools
sudo dkms status # shows parallel-tools
sudo dkms remove -m parallels-tools -v 19.4.0.54962 --all
time sudo make install # 2.51 seconds!

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
