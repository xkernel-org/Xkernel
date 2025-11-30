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
    interproc=false
    indirectcall=false
    upward_interproc=true

    if [ $file == "tests/3_child_param.bc" ]; then
        interproc=true
    elif [ $file == "tests/3_child_param_indirect.bc" ]; then
        interproc=true
    elif [ $file == "tests/8_deeper_child.bc" ]; then
        interproc=true
    elif [ $file == "tests/8_deeper_child_with_effect.bc" ]; then
        interproc=true
    elif [ $file == "tests/9_func_ptr.bc" ]; then
        interproc=true
        indirectcall=true
    elif [ $file == "tests/9_func_ptr_global.bc" ]; then
        interproc=true
        indirectcall=true
    elif [ $file == "tests/9_func_ptr_approximate.bc" ]; then
        interproc=true
        indirectcall=true
    elif [ $file == "tests/10_func_ptr_struct.bc" ]; then
        interproc=true
        indirectcall=true
    fi

    if [ $file == "tests/7_locate_the_right_target.bc" ]; then
        occurence=2
    else
        occurence=1
    fi
    opt -load-pass-plugin=build/libTaintTrackerPass.so \
        -passes="taint-tracker<foo;;3600;false;$interproc;$indirectcall;$upward_interproc;$occurence>" \
        -disable-output \
        $file |& tee ${file%.bc}.results.txt
done
