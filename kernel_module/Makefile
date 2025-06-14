obj-m += kfuncs.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = gcc

# Enable BTF support
EXTRA_CFLAGS += -g -O2

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC) VMLINUX_BTF=/sys/kernel/btf/vmlinux

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
