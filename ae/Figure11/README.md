# Figure 11

## Testbed

1 CloudLab c220g5 machine running Linux 6.14.8-061408-generic with 2+ NUMA
nodes.

## Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and
> `source ~/xk-py/bin/activate` before plotting.

Figure 11 uses the same Linux 6.14.8-061408-generic setup as Figure 10, instead
of the Linux 6.8 kernel used by most other AE experiments. This keeps the
runtime kernel and Xkernel's code-generation source tree aligned for
`NR_MAX_BATCHED_MIGRATION`.

> **Important:** This is a Figure 10/11-specific setup. Do not replace the
> default Linux 6.8 setup for the rest of the artifact. A recommended workflow is
> to reproduce the Linux 6.8 figures first, then reboot into Linux
> 6.14.8-061408-generic for Figure 10 and Figure 11 only. If you already prepared
> this environment for Figure 10, reuse it here.

Prepare the shared Figure 10/11 Linux 6.14.8 environment by following the setup
steps in `../Figure10/README.md` through the Xkernel configuration step. In
particular, reuse the same booted kernel, configured source tree, and toolchain:

```bash
uname -r                         # should show 6.14.8-061408-generic
cd ~/Xkernel
export KERNEL_DIR=~/linux-6.14.8-061408-generic
export CC=gcc-14
export CXX=g++-14

cd ae/Figure11
```

Check NUMA availability, then run the experiment:

```bash
numactl --hardware                # should show at least 2 NUMA nodes
bash install_benchmark.sh         # build NUMA migration benchmark
sudo -E bash run.sh               # runs baseline + tuned values
python3 plot/plot.py              # -> plot/figure11.pdf and plot/figure11_tlb_shootdown_count.pdf
```

By default, `run.sh` clears old files in `results/`, then runs 5 repeats for
each value. The summary appended to each `results/<value>.txt` file reports
averages across those repeats, including each final Probe Latency entry. During
each value's benchmark run, `run.sh` also records `tlb_shootdown.bt`
output to `results/tlb_shootdown_count/<value>.txt`; the companion plot compares
the TLB flush counts for remote shootdown (`reason[1]`) and remote IPI send
(`reason[4]`).

**Machine time:** ~20 minutes &nbsp;|&nbsp; **Human time:** ~1 minute

## Expected Results

Xkernel tunes `NR_MAX_BATCHED_MIGRATION` in `mm/migrate.c` at runtime.
`NR_MAX_BATCHED_MIGRATION` controls the maximum number of pages migrated in a
single batch; the Linux default is 512. This experiment measures probe latency
under a NUMA-migration-heavy workload while sweeping values `{32, 64, 128, 256,
1024}` and comparing them against the default value 512.

The benchmark disables automatic NUMA balancing, creates high migration
pressure with 24 query workers and 2 migration threads, and migrates an 8 GiB
anonymous memory region from NUMA node 1 to NUMA node 0. The generated figure
reports P50/P90/P95/P99 probe latency for each value, and the companion figure
reports TLB shootdown-related flush counts collected by bpftrace.

Representative results from 1 run on CloudLab c220g5 (kernel
6.14.8-061408-generic, 5 repeats per value, averaged Probe Latency summary):

| NR_MAX_BATCHED_MIGRATION | P50 Latency (µs) | P90 Latency (µs) | P95 Latency (µs) | P99 Latency (µs) |
|--------------------------|------------------|------------------|------------------|------------------|
| 32                       | 471.61           | 503.00           | 514.45           | 1244.16          |
| 64                       | 471.77           | 504.23           | 514.54           | 2459.79          |
| 128                      | 472.40           | 507.28           | 533.08           | 5130.91          |
| 256                      | 470.34           | 506.64           | 715.38           | 5979.24          |
| 512 (default)            | 478.09           | 518.80           | 945.06           | 6875.97          |
| 1024                     | 484.14           | 529.31           | 1505.78          | 6468.73          |

**Trend:** Changing `NR_MAX_BATCHED_MIGRATION` changes how much migration work
the kernel performs per batch, exposing a latency/throughput tradeoff in the
migration path. This demonstrates that Xkernel can tune NUMA migration behavior
at runtime without rebuilding or rebooting the kernel.

> **Note:** Exact numbers may vary across runs depending on NUMA topology,
> background load, and memory state. The key observation is the latency tradeoff
> as `NR_MAX_BATCHED_MIGRATION` changes.
