.PHONY: all clean

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86 -I.
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux
BPFTOOL ?= $(shell ls /usr/lib/linux-tools/*/bpftool 2>/dev/null | tail -n 1 || command -v bpftool 2>/dev/null)

BPF_SRCS := $(wildcard stubs/*.bpf.c)
BPF_OBJS := $(BPF_SRCS:.bpf.c=.bpf.o)

all: $(BPF_OBJS)

%.bpf.o: %.bpf.c vmlinux.h
	@test -s vmlinux.h || $(MAKE) -B vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

vmlinux.h:
	@test -n "$(BPFTOOL)" || (echo "bpftool not found" >&2; exit 1)
	$(BPFTOOL) btf dump file $(BTF_FILE) format c > vmlinux.h.tmp
	test -s vmlinux.h.tmp
	mv -f vmlinux.h.tmp vmlinux.h

clean:
	rm -f stubs/*.o
