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

opt -load-pass-plugin=build/libBBSizePass.so \
    -passes="bb-size" \
    -disable-output \
    $KERNEL_DIR/vmlinux.bc |& tee vmlinux-func-bb-sizes.txt
