sudo cat /proc/kallsyms | grep 't update_sd_lb_stats.constprop.0$' | awk '{print $1}'
