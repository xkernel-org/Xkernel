"""Test case definitions for Xkernel code generation pipeline.

Each test case specifies:
  - values: (V1, V2, V3) source-level constant values
  - file: kernel source file containing the constant
  - original: sed search pattern (original source expression)
  - modified: list of replacement expressions [V1->V2, V1->V3]
  - lines: optional line filter for --lines flag
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Testcase:
    name: str
    description: str
    file: str           # kernel source file (e.g. "net/ipv4/tcp_cubic.c")
    original: str       # sed search pattern (original expression)
    modified: list      # [V1->V2 replacement, V1->V3 replacement]
    values: tuple       # (V1, V2, V3)
    lines: str = None   # optional --lines filter
    safe_spans: list = None  # [(func_name, "0xNN", "0xMM"), ...] manual SS ranges


TESTCASES = [
    # Testcase(
    #     name="tcp_cubic",
    #     description="delay_min shift amount",
    #     file="net/ipv4/tcp_cubic.c",
    #     original="ca->delay_min >> 3",
    #     modified=["ca->delay_min >> 2", "ca->delay_min >> 1"],
    #     values=(3, 2, 1),
    #     safe_spans=[("cubictcp_acked", "0x210", "0x21a")]
    # ),
    # Testcase(
    #     name="BLK_MQ_RESOURCE_DELAY",
    #     description="block/blk-mq.c resource delay",
    #     file="block/blk-mq.c",
    #     original="BLK_MQ_RESOURCE_DELAY\t3",
    #     modified=["BLK_MQ_RESOURCE_DELAY\t5", "BLK_MQ_RESOURCE_DELAY\t7"],
    #     values=(3, 5, 7),
    #     safe_spans=[("blk_mq_dispatch_rq_list", "0x32d", "0x395")]
    # ),
    # Testcase(
    #     name="IO_LOCAL_TW_DEFAULT_MAX",
    #     description="io_uring local task work max",
    #     file="io_uring/io_uring.c",
    #     original="#define IO_LOCAL_TW_DEFAULT_MAX\t\t 20",
    #     modified=["#define IO_LOCAL_TW_DEFAULT_MAX\t\t 32",
    #               "#define IO_LOCAL_TW_DEFAULT_MAX\t\t 64"],
    #     values=(20, 32, 64),
    #     safe_spans=[("io_run_task_work_sig", "0x4b", "0x6b"), ("io_uring_try_cancel_requests", "0x97b", "0x152"), 
    #                 ("__do_sys_io_uring_enter", "0x24c", "0x2b9")]
    # ),
    # Testcase(
    #     name="tcp_recovery",
    #     description="tcp_min_rtt shift amount",
    #     file="net/ipv4/tcp_recovery.c",
    #     original="tcp_min_rtt(tp) >> 2",
    #     modified=["tcp_min_rtt(tp) >> 1", "tcp_min_rtt(tp) >> 3"],
    #     values=(2, 1, 3),
    # ),
    # Testcase(
    #     name="BLK_MQ_BUDGET_DELAY",
    #     description="block/blk-mq-sched.c budget delay",
    #     file="block/blk-mq-sched.c",
    #     original="#define BLK_MQ_BUDGET_DELAY\t3",
    #     modified=["#define BLK_MQ_BUDGET_DELAY\t5",
    #               "#define BLK_MQ_BUDGET_DELAY\t7"],
    #     values=(3, 5, 7),
    #     lines="156,248",
    # ),
    # Testcase(
    #     name="BLK_MQ_CPU_WORK_BATCH",
    #     description="block/blk-mq.c BLK_MQ_CPU_WORK_BATCH",
    #     file="block/blk-mq.c",
    #     original="BLK_MQ_CPU_WORK_BATCH",
    #     modified=["16", "32"],
    #     values=(8, 16, 32),
    # ),
    # Testcase(
    #     name="SHRINK_BATCH",
    #     description="mm/shrinker.c SHRINK_BATCH",
    #     file="mm/shrinker.c",
    #     original="#define SHRINK_BATCH 128",
    #     modified=["#define SHRINK_BATCH 32", "#define SHRINK_BATCH 64"],
    #     values=(128,32,64),
    #     safe_spans=[("__pfx_perf_trace_mm_shrink_slab_end","0x10","0x15145")]
    # ),
    Testcase(
        name="NR_MAX_BATCHED_MIGRATION",
        description="mm/migrate.c NR_MAX_BATCHED_MIGRATION",
        file="mm/migrate.c",
        original="#define NR_MAX_BATCHED_MIGRATION\tHPAGE_PMD_NR",
        modified=["#define NR_MAX_BATCHED_MIGRATION\t128",
                "#define NR_MAX_BATCHED_MIGRATION\t256"],
        values=(512, 128, 256),
        safe_spans=[("migrate_pages","0x872","0x877"), ("migrate_pages", "0x8c4", "0x8ca")]
    ),
    # Testcase(
    #     name="BLK_MAX_REQUEST_COUNT",
    #     description="block/blk-mq.c BLK_MAX_REQUEST_COUNT",
    #     file="block/blk-mq.c",
    #     original="BLK_MAX_REQUEST_COUNT",
    #     modified=["8", "16"],
    #     values=(32, 8, 16),
    #     safe_spans=[("blk_start_plug_nr_ios","0x29","0x584"), ("blk_add_rq_to_plug", "0xd1", "0xd5")]
    # ),

]
