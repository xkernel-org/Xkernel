sudo cat /proc/kallsyms | grep 'T task_numa_fault$' | awk '{print $1}'
