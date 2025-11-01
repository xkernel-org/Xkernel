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
    opt -load-pass-plugin=build/libTaintTrackerPass.so \
        -passes="taint-tracker<foo;;3600;false>" \
        -disable-output \
        $file
done
