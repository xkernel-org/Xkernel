

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
|`((cap) * 1280 < (max) * 1024)`  |integer literal|sched|[kernel/sched/fair.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/fair.c#L105)         |-|-|-|-|-|-|
|`((cap1) * 1024 > (cap2) * 1078)`|integer literal|sched|[kernel/sched/fair.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/fair.c#L113)         |-|-|-|-|-|-|
|`*avg += diff / 8;`              |integer literal|sched|[kernel/sched/sched.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched.h#L247)       |-|-|-|-|-|-|
|`2*rq->max_idle_balance_cost;`   |integer literal|sched|[kernel/sched/core.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/core.c#L3747)|-|-|-|-|-|-|
|`RR_TIMESLICE`                   |macro          |sched|[include/linux/sched/rt.h](https://elixir.bootlin.com/linux/v6.14/source/include/linux/sched/rt.h#L82)|-|-|-|-|-|-|
|`.imbalance_pct = 112,`          |integer literal|sched|[kernel/sched/fair.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/fair.c#L2498)|-|-|-|-|-|-|
|`env.imbalance_pct = 100 + (sd->imbalance_pct - 100) / 2;`|integer literal|sched|[kernel/sched/fair.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/fair.c#L2522)|-|-|-|-|-|-|
|`.imbalance_pct = 117,`          |integer literal|sched|[kernel/sched/topology.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/topology.c#L1616)|-|-|-|-|-|-|
|`sd->imbalance_pct = 110;`       |integer literal|sched|[kernel/sched/topology.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/topology.c#L1659)|-|-|-|-|-|-|
|`sd->imbalance_pct = 117;`       |integer literal|sched|[kernel/sched/topology.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/topology.c#L1662)|-|-|-|-|-|-|
|`IOWAIT_BOOST_MIN`               |macro          |sched|[kernel/sched/cpufreq_schedutil.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/cpufreq_schedutil.c#L9)|-|-|-|-|-|-|
|`policy->cur + (policy->cur >> 2);`|integer literal|sched|[kernel/sched/cpufreq_schedutil.c](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/cpufreq_schedutil.c#L140)|-|-|-|-|-|-|
|`runnable_avg_yN_inv`            |const int      |sched|[kernel/sched/sched-pelt.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched-pelt.h#L4)|-|-|-|-|-|-|
|`LOAD_AVG_PERIOD`                |macro          |sched|[kernel/sched/sched-pelt.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched-pelt.h#L13)|-|-|-|-|-|-|
|`LOAD_AVG_MAX`                   |macro          |sched|[kernel/sched/sched-pelt.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched-pelt.h#L14)|-|-|-|-|-|-|
|`MAX_RT_PRIO`                    |macro          |sched|[include/linux/sched/prio.h](https://elixir.bootlin.com/linux/v6.14/source/include/linux/sched/prio.h#L16)|-|-|-|-|-|-|
|`RUNTIME_INF`                    |macro          |sched|[kernel/sched/sched.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched.h#L189)|-|-|-|-|-|-|
|`SCHED_NR_MIGRATE_BREAK`         |macro          |sched|[kernel/sched/sched.h](https://elixir.bootlin.com/linux/v6.14/source/kernel/sched/sched.h#L2840)|-|-|-|-|-|-|




