# Emulate internet network delay, loss, reorder
sudo tc qdisc replace dev ens1f1np1 root netem delay 150ms 50ms loss 5% reorder 5% 10%

# Server:
iperf3 -s

# Client:
iperf3 -c 192.168.6.2 -P 100 -l 4k

# Dump low-level metrics
awk '
/^TcpExt/ {
    if (c++ == 0) {
        for (i=1; i<=NF; i++) h[i] = $i;
    } else {
        for (i=2; i<=NF; i++) {
            if (h[i] ~ /Retrans|Timeout|Sack|Abort|Reno|Lost|FACK|DSACK/) {
                printf "%s: %s\n", h[i], $i;
            }
        }
    }
}' /proc/net/netstat