#!/bin/bash

set -ex

KERNEL_DIR=${KERNEL_DIR:-../linux-wllvm-defconfig}

if [[ ! -d $KERNEL_DIR ]]; then
    echo "KERNEL_DIR not set or does not exist"
    exit 1
fi

if ! command -v opt >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v opt >/dev/null 2>&1; then
        echo "opt not found"
        exit 1
    fi
fi

export LLVM_COMPILER=clang

# Pass option: does it stop when seeing child(), or go into it recursively
INTERPROC=true
# Use vmlinux.bc as input (true, slow) or only the object file (false, fast)
WHOLE_KERNEL=true

### 1. DFR_MAX (1,2)

# %163 = icmp slt i32 %162, 301, !dbg !17437
# Conclusion: [LOCAL]

SOURCE_FILE=net/sunrpc/cache.c
FUNCTION_NAME=cache_check_rcu
SOURCE_OP=icmp
CONSTANT_VALUE=301
OCCURENCE=1

# # %166 = icmp sgt i32 %165, 300, !dbg !17442
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sunrpc/cache.c
# FUNCTION_NAME=cache_check_rcu
# SOURCE_OP=icmp
# CONSTANT_VALUE=300
# OCCURENCE=1

### 2. GSSD_MIN_TIMEOUT

# # %15 = select i1 %14, i32 3600, i32 %13, !dbg !18545
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# FUNCTION_NAME=gss_fill_context
# SOURCE_OP=select
# CONSTANT_VALUE=3600
# OCCURENCE=1

### 3. SMC_TX_WORK_DELAY (1,2)

# Kconfig:
# - CONFIG_INFINIBAND
# - CONFIG_SMC

# # %144 = call zeroext i1 @mod_delayed_work_on(i32 noundef 64, ptr noundef %142, ptr noundef nonnull %143, i64 noundef 0) #8, !dbg !17462
# # Conclusion: [INTERPROC]
#
# SOURCE_FILE=net/smc/smc_tx.c
# FUNCTION_NAME=smc_tx_sndbuf_nonempty
# SOURCE_OP=call
# CONSTANT_VALUE=0
# OCCURENCE=2 # <--- the combination of "call" and "0" is too common, double
#             #      check we are starting at the right instruction

# # %103 = tail call zeroext i1 @queue_delayed_work_on(i32 noundef 64, ptr noundef %101, ptr noundef nonnull %102, i64 noundef 0) #8, !dbg !18394
# # Conclusion: [INTERPROC]
#
# SOURCE_FILE=net/smc/smc_tx.c
# FUNCTION_NAME=smc_tx_consumer_update
# SOURCE_OP=call
# CONSTANT_VALUE=0
# OCCURENCE=3 # <--- the combination of "call" and "0" is too common, double
#             #      check we are starting at the right instruction

### 4. SMC_LGR_NUM_INCR

# # %326 = add i32 %325, 256, !dbg !22204
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/smc/smc_core.c
# FUNCTION_NAME=smc_conn_create
# SOURCE_OP=add
# CONSTANT_VALUE=256
# OCCURENCE=1

### 5. RDS_IB_RECYCLE_BATCH_COUNT

# Kconfig:
# - CONFIG_RDS
# - CONFIG_RDS_RDMA

# # %23 = icmp ult i64 %22, 32, !dbg !15799
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/rds/ib_recv
# FUNCTION_NAME=rds_ib_recv_cache_put
# SOURCE_OP=icmp
# CONSTANT_VALUE=32
# OCCURENCE=1

### 6. QUEUE_THRESHOLD (1,2,3)

# Kconfig:
# - CONFIG_NET_SCH_PIE

# # %25 = icmp ugt i32 %3, 16383, !dbg !12932
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16383
# OCCURENCE=1

# # %42 = icmp ugt i64 %41, 16383, !dbg !12949
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16383
# OCCURENCE=2

# # %61 = icmp ult i32 %3, 16381, !dbg !12962
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16384
# OCCURENCE=1

### 7. PIE_SCALE (1,2,3)

# # %39 = lshr i64 %38, 8, !dbg !12658
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_dump_stats
# SOURCE_OP=lshr
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %14 = shl i32 %2, 8, !dbg !12786
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_calculate_probability
# SOURCE_OP=shl
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %51 = shl i32 %50, 8, !dbg !12956
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=shl
# CONSTANT_VALUE=8
# OCCURENCE=1

### 8. BUSY_POLL_BUDGET (1,2,3,4,5)

# # tail call void @napi_busy_loop_rcu(i32 noundef %61, ptr noundef %46, ptr noundef %45, i1 noundef zeroext %63, i16 noundef zeroext 8) #7, !dbg !13037
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=__io_napi_busy_loop
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # tail call void @napi_busy_loop_rcu(i32 noundef %71, ptr noundef %46, ptr noundef %45, i1 noundef zeroext %73, i16 noundef zeroext 8) #7, !dbg !13060
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=__io_napi_busy_loop
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=2

# # tail call void @napi_busy_loop_rcu(i32 noundef %25, ptr noundef null, ptr noundef null, i1 noundef zeroext %27, i16 noundef zeroext 8) #7, !dbg !13518
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=io_napi_sqpoll_busy_poll
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # tail call void @napi_busy_loop_rcu(i32 noundef %37, ptr noundef null, ptr noundef null, i1 noundef zeroext %39, i16 noundef zeroext 8) #7, !dbg !13527
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=io_napi_sqpoll_busy_poll
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=2

# # %227 = select i1 %226, i16 8, i16 %223, !dbg !16238
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=fs/eventpoll.c
# FUNCTION_NAME=do_epoll_wait
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

OBJ_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).o
BC_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).bc
LL_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).ll
VMLINUX_BC_FILE=$KERNEL_DIR/vmlinux.bc

(
    cd $KERNEL_DIR
    rm -f $OBJ_FILE
    make CC=wllvm AR=llvm-ar HOSTCC=clang $OBJ_FILE
    extract-bc $OBJ_FILE -o $BC_FILE
    llvm-dis $BC_FILE -o $LL_FILE
)

if [[ $WHOLE_KERNEL == true ]]; then
    INPUT_BC_FILE=$VMLINUX_BC_FILE
else
    INPUT_BC_FILE=$KERNEL_DIR/$BC_FILE
fi

opt -load-pass-plugin=build/libTaintTrackerPass.so \
    -passes="taint-tracker<$FUNCTION_NAME;$SOURCE_OP;$CONSTANT_VALUE;false;$INTERPROC;$OCCURENCE>" \
    -disable-output \
    $INPUT_BC_FILE

echo "$KERNEL_DIR/$LL_FILE"
echo "$KERNEL_DIR/$SOURCE_FILE"
