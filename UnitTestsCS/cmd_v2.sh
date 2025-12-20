# 1024,512,256
# sudo python check_assembly_diff.py -f kernel/sched/fair.c -s "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)" \
# "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 512)"
# sudo python check_assembly_diff.py -f kernel/sched/fair.c -s "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)" \
# "#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 256)"

3,2,1
sudo python check_assembly_diff.py -f net/ipv4/tcp_cubic.c -s "ca->delay_min >> 3" "ca->delay_min >> 2"
sudo python check_assembly_diff.py -f net/ipv4/tcp_cubic.c -s "ca->delay_min >> 3" "ca->delay_min >> 1"