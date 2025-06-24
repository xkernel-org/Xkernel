

|Macro|Subsystem|Defined-Sites|Call-Sites|Easy-Hard-to-Attach/Find/Change|Explanation|BPF prog|Workload Analysis and Exp Results|Notes|
|---|---|---|---|---|---|---|---|---|
|IO_LOCAL_TW_DEFAULT_MAX|io_uring|[io_uring.c](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L124)|[1](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L1344), [2](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2360), [3](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2525)|-|-|[io_uring.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/io_uring.bpf.c)|-|-|


