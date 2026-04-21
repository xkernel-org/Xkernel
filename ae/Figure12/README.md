# Figure 12

# Testbed

2 CloudLab xl170 machines. Configure IPs as 192.168.6.1 (server) and 192.168.6.2 (client).

# Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

**Server** (192.168.6.1):

```bash
bash install_nginx.sh server
```

**Client** (192.168.6.2):

```bash
bash install_nginx.sh client
```

**Run experiment** (server):

```bash
sudo bash run.sh
python3 plot/plot.py              # → plot/figure12.pdf
```
