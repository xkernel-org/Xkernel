#!/bin/bash
CPU=${1:-3}
PRE_DATA=$(mktemp)
POST_DATA=$(mktemp)

cleanup() {
    rm -f "$PRE_DATA" "$POST_DATA"
}
trap cleanup EXIT

./metric.sh "$CPU" > "$PRE_DATA"
sudo cyclictest -t 1 -a "$CPU" -p 99 -d 1000 -l 20000
./metric.sh "$CPU" > "$POST_DATA"

echo -e "\n=== Softirq Increment Statistics (After - Before) ==="
awk '
    NR == FNR { pre[$1] = $2; next }
    {
        post_val = $2
        pre_val = (pre[$1] ? pre[$1] : 0)
        diff = post_val - pre_val
        printf "%-20s %10d\n", $1, diff
    }
' "$PRE_DATA" "$POST_DATA"