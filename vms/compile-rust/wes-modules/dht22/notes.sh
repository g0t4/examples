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
# 3.3V - 1
# GND - 6
# GPIO4 - 7

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
# ! seems like I need to use smth else besides what chatgpt generated w/ gpio_* functions... 
#   *** include/linux/gpio/consumer.h # recommended in include/linux/gpio.h 
#   or use the new chardev interface somehow? or?
# ! also maybe I dont need a kernel module to use it first... 
#   ! perhaps test with direct gpio manip and only add the new char dev interface to it when I get DHT22 working to read temp/humidity



# separate naming in sysfs (is this deprecated interface?)
ls /sys/class/gpio
cat /sys/class/gpio/gpiochip571/label # pinctrl-rp1
cat /sys/class/gpio/gpiochip571/ngpio # 54 => means 54 total pins (matches gpuinfo output)
ls -al /sys/class/gpio/gpiochip571 # => ../../devices/platform/axi/1000120000.pcie/1f000d0000.gpio/gpio/gpiochip571

