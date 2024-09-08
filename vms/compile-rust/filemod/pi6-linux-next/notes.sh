# prepare pi6 for testing dht22 sensor

# compile fresh new kernel, minimal config...
cp /boot/config-$(uname -r) ~/linux-next/.config
yes "" | make localmodconfig # strip down + defaults

mkdir ~/configs
cp .config ~/configs/01-localmodconfig

make menuconfig
# search / RASPBERRY
# GPIO_RASPBERRYPI_EXP =y .. probably what I want then... #  TODO ensure GPIO modules/drivers enabled?
# exit dont save

# compile new kernel
time make -j$(nproc) # using gcc this time
time sudo make modules_install
time sudo make install

# issue with initrd/ramfs... just realized I don't need a custom kernel on my pi... just use the stable builtin ones.. I don't need 6.11+ features # probably would need rpi patches or smth anyways...

# FYI current kernel: 6.6.31+rpt-rpi-2712

