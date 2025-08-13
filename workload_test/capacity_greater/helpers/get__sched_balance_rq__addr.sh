sudo cat /proc/kallsyms | grep 't sched_balance_rq$' | awk '{print $1}'
