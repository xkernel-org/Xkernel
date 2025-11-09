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

### 1. DFR_MAX (1)

SOURCE_FILE=net/sunrpc/cache.c
FUNCTION_NAME=cache_check_rcu
SOURCE_OP=icmp
CONSTANT_VALUE=301

### 1. DFR_MAX (2)

SOURCE_FILE=net/sunrpc/cache.c
FUNCTION_NAME=cache_check_rcu
SOURCE_OP=icmp
CONSTANT_VALUE=300

### 2. GSSD_MIN_TIMEOUT

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

# FIXME specify the starting instruction more accurately
SOURCE_FILE=io_uring/napi.c
FUNCTION_NAME=__io_napi_busy_loop
SOURCE_OP="call"
CONSTANT_VALUE=8
INTERPROC=true
WHOLE_KERNEL=true

OBJ_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).o
BC_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).bc
LL_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).ll
VMLINUX_BC_FILE=$KERNEL_DIR/vmlinux.bc

(
    cd $KERNEL_DIR
    extract-bc $OBJ_FILE -o $BC_FILE
    llvm-dis $BC_FILE -o $LL_FILE
)

if [[ $WHOLE_KERNEL == true ]]; then
    INPUT_BC_FILE=$VMLINUX_BC_FILE
else
    INPUT_BC_FILE=$KERNEL_DIR/$BC_FILE
fi

opt -load-pass-plugin=build/libTaintTrackerPass.so \
    -passes="taint-tracker<$FUNCTION_NAME;$SOURCE_OP;$CONSTANT_VALUE;false;$INTERPROC>" \
    -disable-output \
    $INPUT_BC_FILE

echo "$KERNEL_DIR/$LL_FILE"
echo "$KERNEL_DIR/$SOURCE_FILE"
