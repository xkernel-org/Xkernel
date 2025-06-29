

|Name|Type|Subsystem|Defined-Sites|Call-Sites|BPF Prog|Workload Analysis and Exp Results|Notes|
|---|---|---|---|---|---|---|---|
|IO_LOCAL_TW_DEFAULT_MAX|macro|io_uring|[io_uring/io_uring.c](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L124)|[1](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L1344), [2](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2360), [3](https://elixir.bootlin.com/linux/v6.14/source/io_uring/io_uring.c#L2525)|[io_uring.bpf.c](../bpf_kprobe/bpf/examples/io_uring.bpf.c)|[latency_workload.c](../workload_test/io_uring/latency_workload.c)|✅|
|BLK_MQ_CPU_WORK_BATCH|macro|blk|[block/blk-mq.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.h#L39)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L2251), [2](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L4199)|[blk-mq.bpf.c](../bpf_kprobe/bpf/examples/blk-mq.bpf.c)|[blk_mq.fio](../workload_test/blk_mq.fio)|Hard to find gain|
|BLK_MQ_BUDGET_DELAY|macro|blk|[block/blk-mq-sched.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L77)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L156), [2](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq-sched.c#L248)|-|-|Hard to find gain|
|BLK_MQ_RESOURCE_DELAY|macro|blk|[block/blk-mq.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L1996)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L2202)|-|-|-|Hard to find gain|
|THROTL_GRP_QUANTUM|macro|blk|[block/blk-throttle.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L19)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L938), [2](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L938)|-|-|-|
|THROTL_QUANTUM|macro|blk|[block/blk-throttle.c](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L22)|[1](https://elixir.bootlin.com/linux/v6.14/source/block/blk-throttle.c#L993)|-|-|-|
|MAX_GRO_SKBS|macro|net|[net/core/gro.c](https://elixir.bootlin.com/linux/v6.14/source/net/core/gro.c#L8)|[1](https://elixir.bootlin.com/linux/v6.14/source/net/core/gro.c#L539)|[gro_skb.bpf.c](https://github.com/zhongjiechen/Xkernel/blob/main/bpf_kprobe/bpf/examples/gro_skb.bpf.c)|-|WIP|
|MAX_PER_SOCKET_BUDGET|macro|xdp|[net/xdp/xsk.c](https://elixir.bootlin.com/linux/v6.14/source/net/xdp/xsk.c#L36)|[1](https://elixir.bootlin.com/linux/v6.14/source/net/xdp/xsk.c#L425)|-|-|❌ Too much overhead|
|MAX_SOFTIRQ_TIME|macro|softirq|[kernel/softirq.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L482)|[1](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L520)|-|-|Hard to attach|
|MAX_SOFTIRQ_RESTART|macro|softirq|[kernel/softirq.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L483)|[1](https://elixir.bootlin.com/linux/v6.14/source/kernel/softirq.c#L522)|[softirq.bpf.c](../bpf_kprobe/bpf/examples/softirq.bpf.c)|-|Hard to find gain|




