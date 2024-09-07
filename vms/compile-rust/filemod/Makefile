obj-m += filemod.o

# full build process for modules is integrated into the kernel build process, hence why Makefile points to it (=> ~ "make modules")
# linux/Documentation/kbuild/modules.txt
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean