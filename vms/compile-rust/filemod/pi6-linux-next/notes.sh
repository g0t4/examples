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


