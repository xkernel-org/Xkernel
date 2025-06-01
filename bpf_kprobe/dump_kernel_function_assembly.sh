#!/bin/bash

kernel_function_name=${1:-blk_alloc_queue}

lines=$(sudo grep -A1 -E "^[0-9a-fA-F]+ [a-zA-Z] $kernel_function_name$" /proc/kallsyms)

if [[ -z "$lines" ]]; then
  echo "Error: can't find start address for $kernel_function_name in /proc/kallsyms" >&2
  exit 1
fi

start_line=$(echo "$lines" | sed -n '1p')
end_line=$(echo "$lines" | sed -n '2p')

if [[ -z "$end_line" ]]; then
  echo "Error: can't extract end address for $kernel_function_name" >&2
  exit 1
fi

start_addr=$(echo "$start_line" | awk '{print $1}')
end_addr=$(echo "$end_line" | awk '{print $1}')

if [[ -z "$start_addr" || -z "$end_addr" ]]; then
  echo "Error: failed to extract address (start_addr='$start_addr', end_addr='$end_addr')" >&2
  exit 1
fi

echo "$kernel_function_name: $start_addr - $end_addr"

echo "Dumping $kernel_function_name to $kernel_function_name.txt"
sudo objdump -d --start-address=0x$start_addr --stop-address=0x$end_addr /proc/kcore > $kernel_function_name.txt

echo "Done"
