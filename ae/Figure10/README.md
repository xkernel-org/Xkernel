# Figure 10

## Testbed

1 CloudLab c220g5 machine running Linux 6.14.8-061408-generic.

## Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and
> `source ~/xk-py/bin/activate` before plotting.

Figure 10 uses Linux 6.14.8-061408-generic instead of the Linux 6.8 kernel used
by most other AE experiments. `SHRINK_BATCH` controls different Linux code paths
in Linux 6.8 and Linux 6.14. Under this experiment's zswap workload, the two
kernel versions can therefore exhibit different behavior. To reproduce the
performance benefit from tuning `SHRINK_BATCH`, use the Linux 6.14.8 kernel and
the matching Linux 6.14.8 source tree for this figure.

> **Important:** This is a Figure 10/11-specific setup. Do not replace the
> default Linux 6.8 setup for the rest of the artifact. A recommended workflow is
> to reproduce the Linux 6.8 figures first, then reboot into Linux
> 6.14.8-061408-generic for Figure 10 and Figure 11 only.

Install and boot the Linux 6.14.8 kernel:

```bash
wget https://kernel.ubuntu.com/mainline/v6.14.8/amd64/linux-headers-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb \
     https://kernel.ubuntu.com/mainline/v6.14.8/amd64/linux-headers-6.14.8-061408_6.14.8-061408.202505221337_all.deb \
     https://kernel.ubuntu.com/mainline/v6.14.8/amd64/linux-image-unsigned-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb \
     https://kernel.ubuntu.com/mainline/v6.14.8/amd64/linux-modules-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb

# Disable CloudLab DKMS post-install hooks before installing the mainline kernel.
sudo test ! -e /etc/kernel/header_postinst.d/dkms || \
    sudo mv /etc/kernel/header_postinst.d/dkms /etc/kernel/header_postinst.d/dkms.disabled
sudo test ! -e /etc/kernel/postinst.d/dkms || \
    sudo mv /etc/kernel/postinst.d/dkms /etc/kernel/postinst.d/dkms.disabled

sudo dpkg -i \
    linux-headers-6.14.8-061408_6.14.8-061408.202505221337_all.deb \
    linux-headers-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb \
    linux-modules-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb \
    linux-image-unsigned-6.14.8-061408-generic_6.14.8-061408.202505221337_amd64.deb

sudo update-grub
sudo reboot
uname -r                         # should show 6.14.8-061408-generic
```

Prepare the matching Linux 6.14.8 source tree for Xkernel code generation:

Xkernel only needs this as a configured source tree. Do not build or install a
full Linux kernel from this tree for Figure 10. The `make prepare scripts` step
creates the generated headers and host tools that Xkernel needs; during
`xkernel-tool build`, Xkernel compiles the relevant source file itself for the
binary-diff/code-generation step.

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential gcc-14 g++-14 bc bison dwarves elfutils flex libdw-dev \
    libelf-dev libssl-dev ncurses-dev rsync xz-utils

# If you are preparing this source tree manually, this scoped setup command only
# installs the newer pahole needed by Linux 6.14 module BTF when needed.
cd ~/Xkernel
sudo ./xkernel-tool setup --pahole

# The 6.14.8-061408-generic kernel headers use GCC 14-only compiler flags.
# Keep these exports in the shell used to run Figure 10/11 commands.
export CC=gcc-14
export CXX=g++-14

cd ~
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.8.tar.xz
tar -xf linux-6.14.8.tar.xz
mv linux-6.14.8 linux-6.14.8-061408-generic

cd ~/linux-6.14.8-061408-generic
cp /boot/config-$(uname -r) .config
scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS
scripts/config --set-str CONFIG_LOCALVERSION "-061408-generic"
make olddefconfig
make prepare scripts
```

Configure Xkernel from the repository root for the Figure 10/11 AE experiments:

```bash
cd ~/Xkernel

# Install Xkernel dependencies if you have not already run the AE setup.
# This command uses uname -r: Linux 6.14.8-061408-generic gets the Figure 10/11
# GCC 14 + newer-pahole path; other AE kernels use the default dependency path.
./xkernel-tool setup

# Figure 10 and Figure 11 use Linux 6.14.8-061408-generic for AE code generation.
export KERNEL_DIR=~/linux-6.14.8-061408-generic
export CC=gcc-14
export CXX=g++-14

# These Figure 10/11 tunable configs should point to the 6.14.8 source tree.
grep -n 'kernel_dir = "~/linux-6.14.8-061408-generic"' \
    tunables/shrink_batch.toml \
    tunables/nr_max_batched_migration.toml

cd ae/Figure10
```

Run the experiment:

```bash
bash install_zswap_min.sh         # build zswap_min benchmark
sudo -E bash run.sh               # runs baseline + tuned SHRINK_BATCH values
python3 plot/plot.py              # -> plot/figure10.pdf
```

**Machine time:** ~20 minutes &nbsp;|&nbsp; **Human time:** ~1 minutes

## Expected Results

Xkernel tunes `SHRINK_BATCH` in `mm/shrinker.c` at runtime. `SHRINK_BATCH`
controls how many objects the shrinker processes in each batch; the Linux
default is 128. This experiment measures zswap shrinker iteration latency under
memory pressure while sweeping `SHRINK_BATCH` values `{8, 16, 24, 28, 32, 64}`
and comparing them against the default value 128.

The benchmark configures zswap, enables the zswap shrinker, lowers the zswap
pool limit to create memory pressure, and runs `zswap_min` under a constrained
memory cgroup. For each `SHRINK_BATCH` value, the script records per-iteration
latency and CPU usage.

The generated figure reports P50/P90/P99 iteration latency on a log scale, with
CPU usage shown on a secondary axis.

Representative results from 1 run on CloudLab c220g5 (kernel
6.14.8-061408-generic, 500 measured iterations per value):

| SHRINK_BATCH | P50 Latency (µs) | P90 Latency (µs) | P99 Latency (µs) | CPU Usage % |
|--------------|------------------|------------------|------------------|-------------|
| 8            | 29192            | 31074            | 32632            | ~99%        |
| 16           | 30444            | 31732            | 32715            | ~95%        |
| 24           | 30338            | 31421            | 32130            | ~88%        |
| 28           | 104256           | 195870           | 742826           | ~49%        |
| 32           | 117482           | 192465           | 498242           | ~48%        |
| 64           | 127459           | 186202           | 624173           | ~47%        |
| 128 (default)| 96638            | 247257           | 726667           | ~47%        |

**Trend:** Lower `SHRINK_BATCH` values, especially 8–24, substantially reduce
tail shrinker iteration latency compared with the default value 128. The tradeoff
is higher CPU usage because the shrinker performs smaller batches and runs more
actively. This demonstrates the latency/CPU tradeoff that Xkernel can tune at
runtime without rebuilding or rebooting the kernel.

> **Note:** Exact numbers may vary across runs depending on memory pressure,
> swap state, and background system activity. The key observation is the
> latency/CPU tradeoff as `SHRINK_BATCH` changes.
