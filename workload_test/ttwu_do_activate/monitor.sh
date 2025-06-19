#!/bin/bash

sudo cat /sys/kernel/tracing/trace_pipe |\
    sed 's|bpf_trace_printk:||' |\
    python ./plot.py
