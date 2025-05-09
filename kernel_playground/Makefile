obj-m += test.o

# sudo cp /sys/kernel/btf/vmlinux /usr/lib/modules/$(uname -r)/build/

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = x86_64-linux-gnu-gcc-13

# Enable BTF support
EXTRA_CFLAGS += -g -O0

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
