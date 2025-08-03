#!/bin/bash

# Usage: watch -n1 bash numa-maps-monitor.sh <program_name>
#
# This script locates the process, reads its numa_maps, and prints entries
# whose anon>10000.

PROGRAM_NAME=${1:-"benchmark"}

sudo cat /proc/$(pgrep $PROGRAM_NAME)/numa_maps 2>/dev/null |\
    grep -v 'file=' | awk '
        $3 ~ /^anon=/ {
            split($3,a,"=");
            if (a[2] > 10000)
                print $0
        }
    '
