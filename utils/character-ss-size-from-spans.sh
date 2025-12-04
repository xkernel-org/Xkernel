#!/bin/bash

set -ex

python utils/character-ss-size-from-spans.py vmlinux-func-bb-sizes.txt

NUM_SS_SIZE_FILES=$(ls kernel-results/*/ss-size2.txt | wc -l)

if [[ $NUM_SS_SIZE_FILES -ne 136 ]]; then
    echo "Error: Expected 136 ss-size2.txt files, but found $NUM_SS_SIZE_FILES"
    exit 1
fi

for f in kernel-results/*/ss-size2.txt; do
    grep -E "Total: [0-9]+ instructions" $f
done | awk '{ print $2 }' | tee kernel-results/per-perf-const-size.txt

NUM_SIZES=$(cat kernel-results/per-perf-const-size.txt | wc -l)
if [[ $NUM_SIZES -ne 136 ]]; then
    echo "Error: Expected 136 sizes, but found $NUM_SIZES"
    exit 1
fi

python utils/plot_cdf.py kernel-results/per-perf-const-size.txt
