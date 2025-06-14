.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux

all: kprobe_loader bpf/kprobe.bpf.o

bpf/kprobe.bpf.o: bpf/kprobe.bpf.c vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

vmlinux.h:
	sudo bpftool btf dump file $(BTF_FILE) format c > bpf/vmlinux.h

SRCS := $(wildcard *.cc)
OBJS := $(SRCS:.cc=.o)

kprobe_loader: $(OBJS)
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -o $@ $^ -lbpf -lelf -lz

%.o: %.cc
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -c $< -o $@

clean:
	rm -f kprobe_loader bpf/*.o