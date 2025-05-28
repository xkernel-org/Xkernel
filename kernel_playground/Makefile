obj-m += test.o

# sudo cp /sys/kernel/btf/vmlinux /usr/lib/modules/$(uname -r)/build/

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = gcc

# Enable BTF support
EXTRA_CFLAGS += -g -O3

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
