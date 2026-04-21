# Figure 18

Per-task transition delay CDF: Linux KLP (kpatch) vs XKernel.

## Testbed

2 CloudLab machines with a direct link. Configure IPs as `192.168.100.1` (server/sender) and `192.168.100.2` (client/receiver) on the experiment NIC (`enp23s0f0np0`).

## Prerequisites

Set `KERNEL_DIR` if the kernel source is not at `~/linux-6.8.0`:

```bash
export KERNEL_DIR=/path/to/linux-6.8.0
```

## Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

All commands are run on the **server** (192.168.100.1, the sender side):

```bash
bash ../setup_ssh.sh                # one-time SSH key setup
sudo bash install_bench.sh          # installs kpatch, builds kpatch module (~15 min)
sudo bash run.sh                    # ~10 min (Phase 1: KLP, Phase 2: XKernel)
python3 plot/plot.py                # → plot/figure18.pdf
```

### Estimated time

| Step                  | Time       |
|-----------------------|------------|
| `install_bench.sh`    | ~15 min    |
| `run.sh` Phase 1 (KLP)    | ~3 min |
| `run.sh` Phase 2 (XKernel)| ~3 min |
| Total                 | ~20 min    |

> `install_bench.sh` is dominated by `kpatch-build` which recompiles the kernel twice (uses all available cores). The kpatch module is cached after the first build.

## Expected results

128 iperf3 threads with `-w 4k` over a 300 ms RTT link (netem 150 ms each side). Each thread is blocked inside `tcp_sendmsg_locked` waiting for TCP window space.

| Metric              | Linux KLP (kpatch) | XKernel (Mode 1) |
|----------------------|--------------------|-------------------|
| Tasks transitioned   | 128                | ~129              |
| P50 delay            | ~15.5 s            | ~2–5 µs           |
| Max delay            | ~15.5 s            | ~5–37 µs          |
| Transition mechanism | Stack-check on ctx switch | Guard kprobe at SS entry |

**Key takeaway:** KLP delays are on the order of **seconds** because KLP must wait for every thread to voluntarily exit `tcp_sendmsg_locked` (triggered by the KLP stall-detection + forced signaling after ~15 s). XKernel transitions each thread at its next entry to the safe span, completing in **microseconds**.

The exact KLP delay depends on the KLP stall timeout (kernel default ~15 s). XKernel per-task transition time is consistently in the single-digit microsecond range.
