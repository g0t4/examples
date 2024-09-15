# obj-m += dht22fs.o # first impl
# obj-m += dht22fs-gpiod.o # second impl (gpio_ => gpiod_)
obj-m += dht22iio.o # third impl (filesystem char dev => iio_)
obj-m += dht22iio-irq.o
# obj-m += dht22iio-irq.o # fourth impl (iio_ => iio-irq_) MAYBE

.PHONY: all clean copy_driver remove_driver fix_kernel_and_headers dtbo

all: dtbo
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

dtbo: dht22iio-overlay.dts
	dtc -O dtb -o dht22iio.dtbo dht22iio-overlay.dts

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install_driver: all
	sudo cp dht22iio.dtbo /boot/firmware/overlays/
	sudo mkdir -p "/lib/modules/$(shell uname -r)/kernel/drivers/iio/humidity/"
	sudo cp dht22iio.ko "/lib/modules/$(shell uname -r)/kernel/drivers/iio/humidity/"
	sudo depmod -a

status_driver:
	lsmod | grep touch || true
	#
	dtoverlay -l | grep touch || true # IIUC loaded after boot w/ dtoverlay cmd
	#
	dtoverlay -a | grep touch || true # all overlays (loaded and/or not loaded but in search path [boot/firmware/overlays])
	#
	ls -al /boot/firmware/overlays/dht22* || true
	#
	ls -al "/lib/modules/$(shell uname -r)/kernel/drivers/iio/humidity/dht22"* || true

remove_driver:
	sudo rm /boot/firmware/overlays/dht22iio.dtbo || true
	sudo rm "/lib/modules/$(shell uname -r)/kernel/drivers/iio/humidity/dht22iio.ko" || true
	sudo depmod -a

# i.e. when invoking the nested kernel build system, if shit goes sideways and it starts redoing config or otherwise... this can put things back the way they should be:
fix_kernel_and_headers:
	# reinstall packages for current kernel:
	sudo apt install --reinstall "linux-headers-$(shell uname -r)" \
	   "linux-image-$(shell uname -r)"