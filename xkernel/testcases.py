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


TESTCASES = [
    # Testcase(
    #     name="tcp_cubic",
    #     description="delay_min shift amount",
    #     file="net/ipv4/tcp_cubic.c",
    #     original="ca->delay_min >> 3",
    #     modified=["ca->delay_min >> 2", "ca->delay_min >> 1"],
    #     values=(3, 2, 1),
    # ),
    # Testcase(
    #     name="BLK_MQ_RESOURCE_DELAY",
    #     description="block/blk-mq.c resource delay",
    #     file="block/blk-mq.c",
    #     original="BLK_MQ_RESOURCE_DELAY\t3",
    #     modified=["BLK_MQ_RESOURCE_DELAY\t5", "BLK_MQ_RESOURCE_DELAY\t7"],
    #     values=(3, 5, 7),
    # ),
    # Testcase(
    #     name="IO_LOCAL_TW_DEFAULT_MAX",
    #     description="io_uring local task work max",
    #     file="io_uring/io_uring.c",
    #     original="#define IO_LOCAL_TW_DEFAULT_MAX\t\t 20",
    #     modified=["#define IO_LOCAL_TW_DEFAULT_MAX\t\t 32",
    #               "#define IO_LOCAL_TW_DEFAULT_MAX\t\t 64"],
    #     values=(20, 32, 64),
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
    Testcase(
        name="BLK_MQ_CPU_WORK_BATCH",
        description="block/blk-mq.c BLK_MQ_CPU_WORK_BATCH",
        file="block/blk-mq.c",
        original="BLK_MQ_CPU_WORK_BATCH",
        modified=["16", "32"],
        values=(8, 16, 32),
    )
]
