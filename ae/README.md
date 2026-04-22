# Artifact Evaluation for "Xkernel: Rethinking Performance Tunability of Operating System Kernels" (OSDI '26)

## 1. Overview

### 1.1 Artifact Goals
In this paper, we make the following claims:
- Xkernel enables tuning consts for **adapting to hardware devices and workload patterns**. (i.e., `BLK_MAX_REQUEST_COUNT` in Figure 1)
- Xkernel enables tuning consts for **balancing cost-benefit tradeoffs**. (i.e., `MAX_SOFT_IRQ_RESTART` in Figure 9)
- Xkernel enables tuning consts for **controlling kernel internal behavior**. (i.e., `SHRINK_BATCH` in Figure 10)
- Xkernel enables tuning consts with **kernel and hardware observability**. (i.e., `NR_MAX_BATCHED_MIGRATION` in Figure 11)
- Xkernel enables **collective tuning of interdependent consts**. (i.e., `HYSTART_DELAY_[MAX,MIN,factor]` in Figure 12)
- Xkernel introduces **negligible overhead** at runtime. (i.e., Figure 16)
- Xkernel has **lower transition latency than Linux KLP**. (i.e., Figure 18)

We also provide a dataset characterization of perf-consts in the Linux kernel (Figures 13-14) and ad-hoc design drill-down measurements for understanding the Xkernel deployment pipeline (Figure 17) and global convergence overhead (Figures 19-20).

This artifact evaluation package reproduces all figures from the paper. Each figure corresponds to a self-contained experiment with detailed instructions in its `README.md` (under `ae/Figure*/`). Figure1/9/10/11/12/16 needs to be reproduced by running the corresponding experiment, while Figure13-14/17/19-20 (which are dataset-related or ad-hoc design drill-down) are plot-only and can be generated from the provided raw data.

### 1.2 Artifact Structure

The artifact evaluation requires **5 CloudLab machines** provisioned via **3 CloudLab profiles** (under `ae/cloudlab-profiles/`).

| Profile | Nodes | Hardware | Cluster | Used By |
|---------|-------|----------|---------|---------|
| `c220g5.xml` | 1 | c220g5 | Wisconsin | Figure 1(a), 10, 11 |
| `c6620.xml` | 2 | c6620  | Clemson | Figures 1(b), 16, 18 |
| `xl170.xml` | 2 | xl170 | Utah | Figures 9, 12|

Each experiment directory (`ae/Figure*/`) follows a common three-script structure:

1. **`install_*.sh`** — Installs environment dependencies (benchmarks, libraries, etc.).
2. **`run.sh`** — Runs the experiment and saves raw data to `results/`.
3. **`plot/plot.py`** — Generates the corresponding figure from the paper.

Refer to the `README.md` inside each `Figure*/` directory for detailed instructions.

> **Note:** `run.sh`is designed to be **idempotent** (safe to re-run), though rare corner cases (e.g., unexpected interruption) may require manual cleanup before retrying.


### 1.3 Artifact Time

- Install Xkernel in parallel on three machines ([Section 2.3](#23-install-xkernel)) — ⏱ **20-30 min**

- Run experiments in parallel

    | Machine | Figures | Est. Time |
    |---------|---------|-----------|
    | `c220g5` | 1(a) → 10 → 11 | ⏱ **5 min + TODO + TODO** |
    | `c6620` | 1(b) → 16 → 18 | ⏱ **5 min + 10 min + 40min** |
    | `xl170` | 9 → 12 | ⏱ **20 min + 10 min** |
    | `Your laptop` | 13-14, 17, 19-20 | ⏱ **5 min** |

If you have any questions, feel free to contact us via email or HotCRP.

## 2. Setting up [CloudLab](https://www.cloudlab.us/) Machines

If you are a first-time CloudLab user, please read [CloudLab For Artifact Evaluation](https://docs.cloudlab.us/repeatable-research.html#%28part._aec-members%29) for an overview of the process. 

If you do not already have a CloudLab account, please apply for one [here](https://www.cloudlab.us/signup.php) and ask the OSDI AEC chair to add you to the AEC project. Please let us know if you have trouble accessing CloudLab — we can help set up experiments and give you access.

### 2.1. Reserve Nodes

Machines may not always be available. To guarantee availability, click **Experiments → Reserve Nodes** from the CloudLab dashboard. Select the appropriate cluster and hardware type (see table above), specify the number of nodes and your desired time window, then submit the request. See [Resource Reservation](http://docs.cloudlab.us/reservations.html) for details.

### 2.2. Create Experiments Using Profiles

We provide three CloudLab profile XML files under `ae/cloudlab-profiles/`.

To use a profile:

1. Go to **Experiments → Create Experiment Profile**.
2. Click **Upload** and select the corresponding XML file (e.g., `xl170.xml`).
3. Give the profile a name and click **Create**.
4. Click **Instantiate** on the profile page, then keep clicking **Next** / **Finish**.
5. Wait for **Status** to become `Ready` on the experiment page.
6. Access each node via `ssh` using the hostname shown on the experiment page.

### 2.3. Install Xkernel
Please install Xkernel on **three** machines--c220g5, c6620 with IP 192.168.100.1, and xl170 with IP 192.168.6.1 before running the experiments. 

> **Note:** There is no need to install Xkernel on all c6620 and xl170 machines.

```bash
git clone https://github.com/zhongjiechen/Xkernel.git
cd Xkernel
./xkernel-tool setup # about 20-30minutes, depending on the machine.
export KERNEL_DIR=~/linux-6.8.0
```
