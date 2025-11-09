obj-m += kfuncs.o
obj-$(RAW_TEXT_POKE) += raw_text_poke.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC = gcc-14
BTF_VMLINUX = /sys/kernel/btf/vmlinux

# Enable BTF support
# EXTRA_CFLAGS += -g -O2 -DBPF_TEXT_POKE
EXTRA_CFLAGS += -g -O2 

all:
	@if [ ! -f $(KERNELDIR)/vmlinux ] && [ -f $(BTF_VMLINUX) ]; then \
		echo "Linking BTF from $(BTF_VMLINUX) to $(KERNELDIR)/vmlinux"; \
		sudo ln -sf $(BTF_VMLINUX) $(KERNELDIR)/vmlinux; \
	fi
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
