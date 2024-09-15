# obj-m += dht22fs.o # first impl
# obj-m += dht22fs-gpiod.o # second impl (gpio_ => gpiod_)
obj-m += dht22iio.o # third impl (filesystem char dev => iio_)
# obj-m += dht22iio-irq.o # fourth impl (iio_ => iio-irq_) MAYBE

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

# TODO install (after touch install works)
