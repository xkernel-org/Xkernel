# Figure 9

# Testbed

2 CloudLab xl170 machines. Configure IPs as 192.168.6.1 (server) and 192.168.6.2 (client).

# Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

**Server** (192.168.6.1):

```bash
bash install_cyclictest.sh
iperf3 -s -p 5200 & iperf3 -s -p 5201 & iperf3 -s -p 5202 &
```

**Client** (192.168.6.2):

```bash
bash client.sh 192.168.6.1
```

**Run experiment** (server):

```bash
sudo bash run.sh 3         # results → results/figure9.csv
python3 plot/plot.py        # → plot/figure9.pdf
```
