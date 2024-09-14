# I want to know if I can take the same overlay and load it twice with a diff param for gpiopin each time and YES it works with the dht11 overlay
sudo dtoverlay dht11 gpiopin=17
sudo dtoverlay dht11 gpiopin=27

ls /sys/bus/iio/devices/ 
# iio:device0  iio:device1

# dump both temps!
bat /sys/bus/iio/devices/iio:device*/in_temp_input
bat /sys/bus/iio/devices/iio:device*/in_humidityrelative_input

# TODO => find out what I need to change for my touch overlay to get it to load multiple times

# dt overlay info:
dtoverlay -l
# Overlays (in load order):
# 0:  dht11  gpiopin=17
# 1:  dht11  gpiopin=27

sudo lsmod | grep dht
# dht11                  49152  0
# industrialio          114688  2 iio_hwmon,dht11

# 1 driver, 2 overlay instances (from same overlay)

dtoverlay -l -v
# DTOVERLAY[debug]: using platform 'bcm2712'
# DTOVERLAY[debug]: overlay map loaded
# Overlays (in load order):
# 0:  dht11  gpiopin=17
# 1:  dht11  gpiopin=27

# inspect device tree
dtc -I fs /proc/device-tree
# ... interesting output:
# <stdout>: Warning (unique_unit_address): /dht11@11: duplicate unit-address (also used in node /iio-hwmon@11)
# <stdout>: Warning (unique_unit_address): /dht11@1b: duplicate unit-address (also used in node /iio-hwmon@1b)
#    looks like dht11@4 was changed to dht11@11 (0x11 == 17) and dht11@1b (0x1b == 27)

# in dht11-overlay.dts => dht11: dht11@4 
#   label: node@unit-address
#     label = dht11
#     node = dht11@4
#     unit-address = <0x4>
#
# I suspect that you change the unit-address to allow for multiple instances of this node...
#    			<&dht11>,"reg:0", # THIS SEEMS LIKE the change that is needed to alter the address?

# to confirm here is 
dtc -I fs /proc/device-tree # select output:
#
# 	dht11@1b {
# 		pinctrl-names = "default";
# 		pinctrl-0 = <0x11e>;
# 		#io-channel-cells = <0x01>;
# 		compatible = "dht11";
# 		status = "okay";
# 		phandle = <0x11f>;
# 		gpios = <0x38 0x1b 0x00>;
# 	};
#
# 	dht11@11 {
# 		pinctrl-names = "default";
# 		pinctrl-0 = <0x11a>;
# 		#io-channel-cells = <0x01>;
# 		compatible = "dht11";
# 		status = "okay";
# 		phandle = <0x11b>;
# 		gpios = <0x38 0x11 0x00>;
# 	};
#
#
# see how @11/1b are altered in that same @address spot (has to be due to overriding "reg:0")

