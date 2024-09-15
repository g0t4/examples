obj-m += touch.o

.PHONY: all clean copy_driver remove_driver fix_kernel_and_headers

all: dtbo
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

dtbo: touch-sensor-unified.dts
	dtc -O dtb -o touch-sensor-unified.dtbo touch-sensor-unified.dts

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install_driver: all
	sudo cp touch-sensor-unified.dtbo /boot/firmware/overlays/
	sudo mkdir -p "/lib/modules/$(shell uname -r)/kernel/drivers/input/touch/"
	sudo cp touch.ko "/lib/modules/$(shell uname -r)/kernel/drivers/input/touch/"
	# depmod -a

status_driver:
	lsmod | grep touch || true
	#
	dtoverlay -l | grep touch || true
	#
	ls /boot/firmware/overlays/touch*.dtbo || true
	#
	ls "/lib/modules/$(shell uname -r)/kernel/drivers/input/touch" || true

remove_driver:
	sudo rm /boot/firmware/overlays/touch-sensor-unified.dtbo || true
	sudo rm "/lib/modules/$(shell uname -r)/kernel/drivers/input/touch/touch.ko" || true
	# sudo depmod -a

# i.e. when invoking the nested kernel build system, if shit goes sideways and it starts redoing config or otherwise... this can put things back the way they should be:
fix_kernel_and_headers:
	# reinstall packages for current kernel:
	sudo apt install --reinstall "linux-headers-$(shell uname -r)" \
	   "linux-image-$(shell uname -r)"
