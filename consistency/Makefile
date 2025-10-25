obj-m += xk-consistency.o

xk-consistency-objs := core.o kprobe.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = gcc

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
