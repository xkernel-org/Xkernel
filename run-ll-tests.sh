#!/bin/bash

set -ex

if ! command -v clang >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v clang >/dev/null 2>&1; then
        echo "clang not found"
        exit 1
    fi
fi

rm -rf ll_tests/*.bc ll_tests/*.dis.ll ll_tests/*.results.txt

for file in ll_tests/*.ll; do
    llvm-as $file -o ${file%.ll}.bc
    llvm-dis ${file%.ll}.bc -o ${file%.ll}.dis.ll
done

for file in ll_tests/*.bc; do
    interproc=false
    indirectcall=false
    upward_interproc=true
    occurence=1

    opt -load-pass-plugin=build/libTaintTrackerPass.so \
        -passes="taint-tracker<foo;;3600;false;$interproc;$indirectcall;$upward_interproc;$occurence>" \
        -disable-output \
        $file |& tee ${file%.bc}.results.txt
done
