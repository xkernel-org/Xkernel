

|Name|Type|Subsystem|Defined-Sites|Call-Sites|Easy-Hard-to-Attach/Find/Change|Explanation|BPF prog|Workload Analysis and Exp Results|Notes|
|---|---|---|---|---|---|---|---|---|---|
|IO_LOCAL_TW_DEFAULT_MAX|macro|io_uring|[io_uring/io_uring.c](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L124)|[1](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L1344), [2](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2360), [3](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2525)|-|-|[io_uring.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/io_uring.bpf.c)|-|-|
|BLK_MQ_BUDGET_DELAY|macro|blk_mq|[block/blk-mq-sched.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L77)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L156), [2](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L248)|-|-|[blk-mq.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/blk-mq.bpf.c)|-|-|
|BLK_MQ_RESOURCE_DELAY|macro|blk_mq|[block/blk-mq.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L1996)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L2202)|-|-|[blk-mq.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/blk-mq.bpf.c)|-|-|
|MAX_GRO_SKBS|macro|net|[net/core/gro.c](https://elixir.bootlin.com/linux/v6.14/source/net/core/gro.c#L8)|[1](https://elixir.bootlin.com/linux/v6.14/source/net/core/gro.c#L539)|-|-|[gro_skb.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/gro_skb.bpf.c)|-|-|
|MAX_PER_SOCKET_BUDGET|macro|xdp|[net/xdp/xsk.c](https://elixir.bootlin.com/linux/v6.14/source/net/xdp/xsk.c#L36)|[1](https://elixir.bootlin.com/linux/v6.14/source/net/xdp/xsk.c#L425)|-|-|-|-|-|
|MAX_SOFTIRQ_TIME|macro|softirq|[kernel/softirq.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L482)|[1](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L520)|-|-|-|-|-|
|MAX_SOFTIRQ_RESTART|macro|softirq|[kernel/softirq.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L483)|[1](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L522)|-|-|-|-|-|
|THROTL_GRP_QUANTUM|macro|blk|[block/blk-throttle.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L19)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L938), [2](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L938)|-|-|-|-|-|
|THROTL_QUANTUM|macro|blk|[block/blk-throttle.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L22)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L993)|-|-|-|-|-|




