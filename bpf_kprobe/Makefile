.PHONY: all clean $(BPF_PROGS)

BPF_CLANG=clang
BPF_CFLAGS=-g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/
LIBBPF_DIR=/usr/include/bpf
BTF_FILE=/sys/kernel/btf/vmlinux

# 所有 BPF 源文件
BPF_SRCS  := $(wildcard bpf/examples/*.bpf.c)
BPF_OBJS  := $(BPF_SRCS:.bpf.c=.bpf.o)
# 提取程序名（例如 aio_plug, shrink_batch）
BPF_PROGS := $(notdir $(BPF_SRCS:.bpf.c=))

# 默认：全部编译
all: kprobe_loader $(BPF_OBJS)

# 每个 bpf.o 都依赖 vmlinux.h
%.bpf.o: %.bpf.c bpf/vmlinux.h
	$(BPF_CLANG) $(BPF_CFLAGS) -I$(LIBBPF_DIR) -c $< -o $@

# 生成头文件
bpf/vmlinux.h:
	sudo bpftool btf dump file $(BTF_FILE) format c > $@

# C++ loader
SRCS := $(wildcard *.cc)
OBJS := $(SRCS:.cc=.o)

kprobe_loader: $(OBJS)
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -o $@ $^ -lbpf -lelf -lz -lgflags

%.o: %.cc
	g++ -g -O3 -Wall -I$(LIBBPF_DIR) -c $< -o $@

# 支持 make aio_plug shrink_batch
# 每个 BPF 程序名作为伪目标：
# make aio_plug         → 编译 bpf/examples/aio_plug.bpf.o
# make aio_plug shrink_batch → 两个都编译
$(BPF_PROGS): %: kprobe_loader bpf/examples/%.bpf.o
	@echo "Built BPF program: $@"

clean:
	rm -f kprobe_loader bpf/*.o bpf/examples/*.o *.o bpf/vmlinux.h
