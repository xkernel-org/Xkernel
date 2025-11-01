#!/bin/bash

set -ex

export PATH=/usr/lib/llvm-20/bin:$PATH

# We use -disable-output and -o /dev/null because we only care about the
# printouts (errs()) from our pass, not a modified .bc file.
opt -load-pass-plugin=build/libTaintTrackerPass.so -passes="taint-tracker" \
    -disable-output \
    /media/wd-sn580-2t-1/users/wentaoz5/xkernel/defuse/linux-wllvm/net/sunrpc/auth_gss/auth_gss.bc
