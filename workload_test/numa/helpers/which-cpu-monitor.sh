#!/bin/bash

# Usage: watch -n1 bash which-cpu-monitor.sh <program_name>
#
# This script locates the process and finds which CPU(s) it is running on

PROGRAM_NAME=${1:-"benchmark"}

ps -L -o pid,tid,psr,nlwp,comm -p $(pgrep $PROGRAM_NAME) 2>/dev/null |\
     tail -n+2 | awk '{ print $3 }' | paste -sd,
