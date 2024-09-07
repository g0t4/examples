# obj-m => means that the filemod.o file is a loadable module, in kernel tree you might have obj-y, IIUC
obj-m += filemod.o

# full build process for modules is integrated into the kernel build process, hence why Makefile points to it (=> ~ "make modules")
# 	linux/Documentation/kbuild/modules.txt
#   linux/Documentation/kbuild/makefiles.rst # for more info on Makefiles, like this one
#   bat /lib/modules/$(uname -r)/build/Makefile  # see Makefile for modules target
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean