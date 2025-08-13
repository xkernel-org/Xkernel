.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux

BPF_SRCS := $(wildcard bpf/examples/*.bpf.c)
BPF_OBJS := $(BPF_SRCS:.bpf.c=.bpf.o)

all: kprobe_loader $(BPF_OBJS)

bpf/examples/numa_scan_poke.bpf.o: BPF_CFLAGS += -DNEW_NUMA_PERIOD_THRESHOLD=7 -DSYMBOL_BASE_ADDRESS=0x$(shell sudo cat /proc/kallsyms | grep 'T task_numa_fault$$' | awk '{print $$1}')
bpf/examples/capacity_greater_poke.bpf.o: BPF_CFLAGS += -DSYMBOL_BASE_ADDRESS1=0x$(shell sudo cat /proc/kallsyms | grep 't update_sd_lb_stats.constprop.0$$' | awk '{print $$1}') -DSYMBOL_BASE_ADDRESS2=0x$(shell sudo cat /proc/kallsyms | grep 't sched_balance_rq$$' | awk '{print $$1}')

%.bpf.o: %.bpf.c bpf/vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

bpf/vmlinux.h:
	sudo bpftool btf dump file $(BTF_FILE) format c > bpf/vmlinux.h

SRCS := $(wildcard *.cc)
OBJS := $(SRCS:.cc=.o)

kprobe_loader: $(OBJS)
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -o $@ $^ -lbpf -lelf -lz -lgflags

%.o: %.cc
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -c $< -o $@

clean:
	rm -f kprobe_loader bpf/vmlinux.h bpf/examples/*.o *.o