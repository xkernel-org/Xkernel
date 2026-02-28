.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86 -I.
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux

BPF_SRCS := $(wildcard stubs/*.bpf.c)
BPF_OBJS := $(BPF_SRCS:.bpf.c=.bpf.o)

all: $(BPF_OBJS)

%.bpf.o: %.bpf.c vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

vmlinux.h:
	sudo bpftool btf dump file $(BTF_FILE) format c > vmlinux.h

clean:
	rm -f stubs/*.o
