#!/bin/bash
cpu=${1:-1}
cat /proc/softirqs | awk 'NR>1 {print $1, $'$((cpu+2))'}'