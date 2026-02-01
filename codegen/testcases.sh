# 1024,512,256
# sudo python check_assembly_diff.py -f kernel/sched/fair.c -s "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)" \
# "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 512)"
# sudo python check_assembly_diff.py -f kernel/sched/fair.c -s "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)" \
# "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 256)"

# tcp_cubic: delay_min shift amount
3,2,1
sudo python check_assembly_diff.py -f net/ipv4/tcp_cubic.c -s "ca->delay_min >> 3" "ca->delay_min >> 2"
sudo python check_assembly_diff.py -f net/ipv4/tcp_cubic.c -s "ca->delay_min >> 3" "ca->delay_min >> 1"

# blk-mq: BLK_MQ_RESOURCE_DELAY
3,5,7
sudo python check_assembly_diff.py -f block/blk-mq.c -s "BLK_MQ_RESOURCE_DELAY	3" "BLK_MQ_RESOURCE_DELAY	5" --lines 2202
sudo python check_assembly_diff.py -f block/blk-mq.c -s "BLK_MQ_RESOURCE_DELAY	3" "BLK_MQ_RESOURCE_DELAY	7" --lines 2202

# io_uring: IO_LOCAL_TW_DEFAULT_MAX
20,32,64
sudo python check_assembly_diff.py -f io_uring/io_uring.c -s "#define IO_LOCAL_TW_DEFAULT_MAX		 20" "#define IO_LOCAL_TW_DEFAULT_MAX		 32"
sudo python check_assembly_diff.py -f io_uring/io_uring.c -s "#define IO_LOCAL_TW_DEFAULT_MAX		 20" "#define IO_LOCAL_TW_DEFAULT_MAX		 64"

# tcp_recovery: tcp_min_rtt shift amount
2,1,3
sudo python check_assembly_diff.py -f net/ipv4/tcp_recovery.c -s "tcp_min_rtt(tp) >> 2" "tcp_min_rtt(tp) >> 1"
sudo python check_assembly_diff.py -f net/ipv4/tcp_recovery.c -s "tcp_min_rtt(tp) >> 2" "tcp_min_rtt(tp) >> 3"

# blk-mq-sched: BLK_MQ_BUDGET_DELAY
3,5,7
sudo python check_assembly_diff.py -f block/blk-mq-sched.c -s "#define BLK_MQ_BUDGET_DELAY	3" "#define BLK_MQ_BUDGET_DELAY	5" --lines 156,248
sudo python check_assembly_diff.py -f block/blk-mq-sched.c -s "#define BLK_MQ_BUDGET_DELAY	3" "#define BLK_MQ_BUDGET_DELAY	7" --lines 156,248
