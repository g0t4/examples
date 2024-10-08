# *** pi6 => compile new kernel (abandoning this, using current, stable kernel)

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


# *** testing dht22 on pi6

# FYI https://lwn.net/Articles/532714/ - GPIO in the kernel


# tentative pins to use:
# 3.3V - physical pin 1
# GND - physical pin 6
# GPIO4 - physical pin 7

# FYI
sudo gpiodetect
sudo gpioinfo # lists state
# gpiochip4 # has 26 GPIO lines just like header docs for rpi (https://projects.raspberrypi.org/en/projects/physical-computing/1), also has away more than 40 total lines but those are just for other things beyond the physical GPIO header IIAC...
sudo gpiofind GPIO4 #  =>  gpiochip4 4
# gpio* commands: https://www.beyondlogic.org/an-introduction-to-chardev-gpio-and-libgpiod-on-the-raspberry-pi/
sudo gpioinfo gpiochip4 # line #4 == GPIO4
sudo gpioget gpiochip4 4 # 0/1 
#   can set bias too
sudo gpiomon gpiochip4 4 # monitor it!
sudo gpioset gpiochip4 4=1 # fails... says device is busy? maybe b/c not connected or misconfigured?
# ok, have to "export" a pin to get its interfaces to show up in sysfs GPIO
#  https://www.ics.com/blog/gpio-programming-using-sysfs-interface
#   YUP DEPRECATED in favor of new ... GPIO character device API (not easily accessible from command line)
#  COVERS BOTH sysfs GPIO and chardev GPIO:
#     https://www.beyondlogic.org/an-introduction-to-chardev-gpio-and-libgpiod-on-the-raspberry-pi/
#     chardev => discovery mechanism (get around hardcoding pin/line #s)
#     FYI linux comes with 
cd tools/gpio/lsgpio.c # kernel source
make
sudo ./lsgpio


# separate naming in sysfs (is this deprecated interface?)
ls /sys/class/gpio
cat /sys/class/gpio/gpiochip571/label # pinctrl-rp1
cat /sys/class/gpio/gpiochip571/ngpio # 54 => means 54 total pins (matches gpuinfo output)
ls -al /sys/class/gpio/gpiochip571 # => ../../devices/platform/axi/1000120000.pcie/1f000d0000.gpio/gpio/gpiochip571



# GPIO kernel guide https://embetronicx.com/tutorials/linux/device-drivers/gpio-driver-basic-using-raspberry-pi/ => simple guide... after reading some of it I get gpio_ methods working (except request but who fucking cares about that ;) )

# drivers/iio/humidity/dht11.c # lolz kernel has a driver for dht11 (and IIAC dht22 the successor)
#   wtf man... "bit banging" sounds like ... wow... as does "banging bits"... ~palindrome :)
#   uses IRQs on edges it seems... 
#      iio_chan_spec # 

# alt => https://github.com/raspberrypi/linux  # pull official rpi kernel source if I wanna compile new kernel

#