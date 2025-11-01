#!/bin/bash

set -ex

export PATH=/usr/lib/llvm-20/bin:$PATH

# We use -disable-output and -o /dev/null because we only care about the
# printouts (errs()) from our pass, not a modified .bc file.
#
# Usage: taint-tracker<function_name;opcode;constant_value;debug>
# - function_name: name of the function to analyze
# - opcode: target instruction opcode (e.g., "store", "call", "add", etc. or empty for all)
# - constant_value: the constant integer value to track
# - debug: verbose debug mode (true/false/1/0, default: false)
#
# Example with parameters:
# opt -load-pass-plugin=build/libTaintTrackerPass.so -passes="taint-tracker<gss_fill_context;store;3600;true>" ...
#
# Using defaults (gss_fill_context, any opcode, 3600, debug off):
opt -load-pass-plugin=build/libTaintTrackerPass.so \
    -passes="taint-tracker<gss_fill_context;select;3600;true>" \
    -disable-output \
    /media/wd-sn580-2t-1/users/wentaoz5/xkernel/defuse/linux-wllvm/net/sunrpc/auth_gss/auth_gss.bc
