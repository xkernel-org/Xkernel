# Figure 12

# Testbed

2 CloudLab xl170 machines. Configure IPs as 192.168.6.1 (server) and 192.168.6.2 (client).

# Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

All commands are run on the **server** (192.168.6.1):

```bash
bash ../setup_ssh.sh                # one-time SSH key setup
bash install_nginx.sh               # installs server + client deps
bash run.sh                         # ~3 minutes
python3 plot/plot.py                # → plot/figure12.pdf
```
