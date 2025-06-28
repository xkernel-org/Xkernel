.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux

BPF_SRCS := $(wildcard bpf/examples/*.bpf.c)
BPF_OBJS := $(BPF_SRCS:.bpf.c=.bpf.o)

all: kprobe_loader $(BPF_OBJS)

%.bpf.o: %.bpf.c vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

vmlinux.h:
	sudo bpftool btf dump file $(BTF_FILE) format c > bpf/vmlinux.h

SRCS := $(wildcard *.cc)
OBJS := $(SRCS:.cc=.o)

kprobe_loader: $(OBJS)
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -o $@ $^ -lbpf -lelf -lz -lgflags

%.o: %.cc
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -c $< -o $@

clean:
	rm -f kprobe_loader bpf/*.o bpf/examples/*.o *.o