#!/bin/bash

set -ex

if ! command -v opt >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v opt >/dev/null 2>&1; then
        echo "opt not found"
        exit 1
    fi
fi

### 1. DFR_MAX (1)

KERNEL_DIR=/media/wd-sn580-2t-1/users/wentaoz5/xkernel/defuse/linux-wllvm
SOURCE_FILE=net/sunrpc/cache.c
FUNCTION_NAME=cache_check_rcu
SOURCE_OP=icmp
CONSTANT_VALUE=301

### 1. DFR_MAX (2)

KERNEL_DIR=/media/wd-sn580-2t-1/users/wentaoz5/xkernel/defuse/linux-wllvm
SOURCE_FILE=net/sunrpc/cache.c
FUNCTION_NAME=cache_check_rcu
SOURCE_OP=icmp
CONSTANT_VALUE=300

### 2. GSSD_MIN_TIMEOUT

KERNEL_DIR=/media/wd-sn580-2t-1/users/wentaoz5/xkernel/defuse/linux-wllvm
SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
FUNCTION_NAME=gss_fill_context
SOURCE_OP=select
CONSTANT_VALUE=3600

# TODO Not compiled in defconfig

### 3. SMC_TX_WORK_DELAY

### 4. SMC_LGR_NUM_INCR

### 5. RDS_IB_RECYCLE_BATCH_COUNT

### 6. QUEUE_THRESHOLD

### 7. PIE_SCALE

### 8. BUSY_POLL_BUDGET

OBJ_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).o
BC_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).bc
LL_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).ll
VMLINUX_BC_FILE=$KERNEL_DIR/vmlinux.bc

(
    cd $KERNEL_DIR
    extract-bc $OBJ_FILE -o $BC_FILE
    llvm-dis $BC_FILE -o $LL_FILE
)

opt -load-pass-plugin=build/libTaintTrackerPass.so \
    -passes="taint-tracker<$FUNCTION_NAME;$SOURCE_OP;$CONSTANT_VALUE;false>" \
    -disable-output \
    $KERNEL_DIR/$BC_FILE \
    `#$VMLINUX_BC_FILE`

echo "$KERNEL_DIR/$LL_FILE"
echo "$KERNEL_DIR/$SOURCE_FILE"
