#!/bin/bash

for f in kernel-results/*/*.time.txt; do
    grep 'Elapsed (wall clock) time' $f
done | awk '{print $8}' | python utils/time_stats.py

TMPFILE=$(mktemp)
for f in kernel-results/*/*.time.txt; do
    grep 'Maximum resident set size (kbytes)' $f
done | awk '{print $6}' | sort -n > $TMPFILE
echo "Max memory: $(tail -n 1 $TMPFILE) kB"
echo "Min memory: $(head -n 1 $TMPFILE) kB"
rm -f $TMPFILE
