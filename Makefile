# Name of the BPF program
BPF_PROG = bpf_prog
KERNEL_DIR = /lib/modules/$(shell uname -r)/build

CLANG = clang

# sudo ln -s /usr/include/x86_64-linux-gnu/asm /usr/include/asm

CFLAGS = -O2 -g -Wall -target bpf -D__TARGET_ARCH_x86 \
	-I/usr/include/bpf \
	-I/usr/src/linux-headers-6.8.0-53-generic/tools/bpf/resolve_btfids/libbpf/include

all: $(BPF_PROG).o

$(BPF_PROG).o: $(BPF_PROG).c
	$(CLANG) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(BPF_PROG).o
