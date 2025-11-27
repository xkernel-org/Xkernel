#!/bin/bash

set -ex

if ! command -v clang >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v clang >/dev/null 2>&1; then
        echo "clang not found"
        exit 1
    fi
fi

rm -rf tests/*.bc tests/*.ll tests/*.results.txt

for file in tests/*.c; do
    clang -g -c -emit-llvm -fdebug-prefix-map="$PWD"=. $file -o ${file%.c}.bc
    clang -g -S -emit-llvm -fdebug-prefix-map="$PWD"=. $file -o ${file%.c}.ll
done
