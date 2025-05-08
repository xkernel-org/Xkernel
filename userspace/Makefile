.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86
LIBBPF_DIR=/usr/include/bpf

all: kprobe_loader bpf/kprobe.bpf.o

bpf/kprobe.bpf.o: bpf/kprobe.bpf.c vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

vmlinux.h:
	sudo bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h

kprobe_loader: kprobe_loader.c
	gcc -g -O2 -Wall -I$(LIBBPF_DIR) -o $@ $< -lbpf -lelf -lz

clean:
	rm -f kprobe_loader bpf/*.o