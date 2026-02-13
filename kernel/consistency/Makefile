obj-m += xk-consistency.o

xk-consistency-objs := core.o kprobe.o

KBUILD_EXTRA_SYMBOLS += $(PWD)/../kfuncs/Module.symvers

ifeq ("$(wildcard $(PWD)/../kfuncs/Module.symvers)","")
$(error You must compile kfuncs first)
endif

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = gcc

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
