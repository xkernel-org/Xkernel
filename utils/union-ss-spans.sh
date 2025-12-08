#!/bin/bash

# From any given perf-const, extract from raw analysis results
# kernel-results/<perf-const>/*.output.txt:
#
# 1. The top-level [begin, end]
# 2. All lower-level functions' full span
#
# and calculate the union.

set -ex

for f in kernel-results/*/*.output.txt; do
    grep "Total: [0-9]\+ instructions" $f | awk '{ print $2 }'
done | tee kernel-results/occurrence-size.txt

python utils/plot_cdf.py kernel-results/occurrence-size.txt

for dir in kernel-results/*; do
    if [[ ! -d $dir ]]; then
        continue
    fi
    python utils/union-ss-spans.py $dir |& tee $dir/ss-size1.txt
done
