obj-m += xk-consistency.o

xk-consistency-objs := core.o kprobe.o

KBUILD_EXTRA_SYMBOLS += $(PWD)/../kfuncs/Module.symvers

ifeq ("$(wildcard $(PWD)/../kfuncs/Module.symvers)","")
$(error You must compile kfuncs first)
endif

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
CC ?= gcc

# Enable DEBUG for verbose stack traces during transition.
# Comment out or use `make DEBUG=0` to disable.
ifneq ($(DEBUG),0)
ccflags-y += -DDEBUG
endif

all:
	make -C $(KERNELDIR) M=$(PWD) modules CC=$(CC)

clean:
	make -C $(KERNELDIR) M=$(PWD) clean
