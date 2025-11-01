# We use -disable-output and -o /dev/null because we only care about the
# printouts (errs()) from our pass, not a modified .bc file.
opt -load=./lib/TaintTrackerPass.so -passes="taint-tracker" \
    -disable-output vmlinux.bc -o /dev/null
