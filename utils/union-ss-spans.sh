#!/bin/bash

# From any given perf-const, extract from raw analysis results
# kernel-results/<perf-const>/*.output.txt:
#
# 1. The top-level [begin, end]
# 2. All lower-level functions' full span
#
# and calculate the union.

set -ex

for dir in kernel-results/*; do
    if [[ ! -d $dir ]]; then
        continue
    fi
    python utils/union-ss-spans.py $dir |& tee $dir/ss-size1.txt
done
