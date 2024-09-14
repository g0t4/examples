obj-m += touch.o

all: dtbo
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

dtbo:
	dtc -O dtb -o touch-sensor-26.dtbo touch-sensor-26.dts
	dtc -O dtb -o touch-sensor-16.dtbo touch-sensor-16.dts

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
