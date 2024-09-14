obj-m += touch.o

all: dtbo
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

dtbo:
	dtc -O dtb -o touch-sensor.dtbo touch-sensor-overlay.dts
	dtc -O dtb -o touch-sensor16.dtbo touch-sensor-16-overlay.dts

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
