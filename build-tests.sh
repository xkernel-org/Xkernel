#!/bin/bash

set -ex

if ! command -v clang >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v clang >/dev/null 2>&1; then
        echo "clang not found"
        exit 1
    fi
fi

for file in tests/*.c; do
    clang -c -emit-llvm $file -o ${file%.c}.bc
    clang -S -emit-llvm $file -o ${file%.c}.ll
done
