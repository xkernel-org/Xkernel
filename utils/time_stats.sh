#!/bin/bash

for f in kernel-results/*/*.time.txt; do
    grep 'Elapsed (wall clock) time' $f
done | awk '{print $8}' | python utils/time_stats.py
