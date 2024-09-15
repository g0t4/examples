obj-m += touch.o

build: dtbo
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

dtbo:
	dtc -O dtb -o touch-sensor-unified.dtbo touch-sensor-unified.dts

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install: build
	cp touch-sensor-unified.dtbo /boot/firmware/overlays/
	cp touch.ko /lib/modules/$(shell uname -r)/kernel/drivers/input/touch/
