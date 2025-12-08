#!/bin/bash

#
# Run the analysis for all kernel-results/*.input.txt files
#

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

# Pass options:
INTERPROC=false
UPWARD_INTERPROC=true
INDIRECT_CALL=false

# Script options:
WHOLE_KERNEL=true

TOTAL=$(ls kernel-results/*/*.input.txt | wc -l)
CURRENT=0

date_start=$(date +%Y-%m-%d\ %H:%M:%S)

for INPUT_FILE in kernel-results/*/*.input.txt; do
    CURRENT=$((CURRENT + 1))
    echo "### [$CURRENT/$TOTAL] $INPUT_FILE, $date_start -> $(date +%Y-%m-%d\ %H:%M:%S)"

    source $INPUT_FILE
    OUTPUT_FILE=$(dirname $INPUT_FILE)/$(basename $INPUT_FILE .input.txt).output.txt
    TIME_STATISTICS=$(dirname $INPUT_FILE)/$(basename $INPUT_FILE .input.txt).time.txt

    OBJ_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).o
    BC_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).bc
    LL_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).ll
    VMLINUX_BC_FILE=$KERNEL_DIR/vmlinux.bc

    if [[ -f $OUTPUT_FILE ]]; then
        echo "Skipping $INPUT_FILE - output already exists"
        continue
    fi

    if [[ $WHOLE_KERNEL != true ]]; then
        pushd $KERNEL_DIR
        rm -f $OBJ_FILE
        make CC=wllvm AR=llvm-ar HOSTCC=clang $OBJ_FILE
        extract-bc $OBJ_FILE -o $BC_FILE
        llvm-dis $BC_FILE -o $LL_FILE
        popd
    fi

    if [[ $WHOLE_KERNEL == true ]]; then
        INPUT_BC_FILE=$VMLINUX_BC_FILE
    else
        INPUT_BC_FILE=$KERNEL_DIR/$BC_FILE
    fi

    /usr/bin/time -o $TIME_STATISTICS -v \
        opt -load-pass-plugin=build/libTaintTrackerPass.so \
        -passes="taint-tracker<$FUNCTION_NAME;$SOURCE_OP;$CONSTANT_VALUE;false;$INTERPROC;$INDIRECT_CALL;$UPWARD_INTERPROC;$OCCURENCE;true>" \
        -disable-output \
        $INPUT_BC_FILE |& tee $OUTPUT_FILE

    echo "" |& tee -a $OUTPUT_FILE
    echo "$KERNEL_DIR/$LL_FILE" |& tee -a $OUTPUT_FILE
    echo "$KERNEL_DIR/$SOURCE_FILE" |& tee -a $OUTPUT_FILE
done
