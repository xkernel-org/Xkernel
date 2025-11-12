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

source .all-cases-run-analysis.sh

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
