#!/bin/bash

set -ex

if ! command -v opt >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v opt >/dev/null 2>&1; then
        echo "opt not found"
        exit 1
    fi
fi

for file in tests/*.bc; do
    if [ $file == "tests/8_deeper_child.bc" ]; then
        interproc=true
    elif [ $file == "tests/8_deeper_child_with_effect.bc" ]; then
        interproc=true
    else
        interproc=false
    fi
    if [ $file == "tests/7_locate_the_right_target.bc" ]; then
        occurence=2
    else
        occurence=1
    fi
    opt -load-pass-plugin=build/libTaintTrackerPass.so \
        -passes="taint-tracker<foo;;3600;false;$interproc;$occurence>" \
        -disable-output \
        $file |& tee ${file%.bc}.results.txt
done
