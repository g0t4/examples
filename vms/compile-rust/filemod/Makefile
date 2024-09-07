# obj-m => means that the filemod.o file is a loadable module, in kernel tree you might have obj-y, obj-n
# 	in fact in kernel tree, you'll find obj-$(CONFIG_FOO) += foo.o # conditionally add as y/m/n
obj-m += filemod.o
#
# add more modules:
# 	obj-m += examples/filemod-legacy-init_module-cleanup_module.o
#  	  # sudo insmod examples/filemod-legacy-init_module-cleanup_module.ko
#
# multifile module:
# 	obj-m += startstop.o
# 	startstop-objs := start.o stop.o



# full build process for modules is integrated into the kernel build process, hence why Makefile points to it (=> ~ "make modules")
# 	linux/Documentation/kbuild/modules.txt
#   linux/Documentation/kbuild/makefiles.rst # for more info on Makefiles, like this one
#   bat /lib/modules/$(uname -r)/build/Makefile  # see Makefile for modules target
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean