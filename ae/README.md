# Artifact Evaluation for "Principled Performance Tunability in Operating System Kernels" (OSDI '25)

## Overview

The artifact evaluation requires **5 CloudLab machines** provisioned via **3 CloudLab profiles**.
Each experiment's `README.md` (under `ae/Figure*/`) contains self-contained instructions;
this document covers only the CloudLab setup.

| Profile | Nodes | Hardware | Cluster | Used By |
|---------|-------|----------|---------|---------|
| `c220g5.xml` | 1 | c220g5 | Wisconsin | Figure 1(a), 10, 11 |
| `c6620.xml` | 2 | c6620  | Clemson | Figures 1(b), 16, 18 |
| `xl170.xml` | 2 | xl170 | Utah | Figures 9, 12|

If you have any questions, feel free to contact us via email or HotCRP.

## Setting up [CloudLab](https://www.cloudlab.us/) Machines

If you are a first-time CloudLab user, please read [CloudLab For Artifact Evaluation](https://docs.cloudlab.us/repeatable-research.html#%28part._aec-members%29) for an overview of the process. 

If you do not already have a CloudLab account, please apply for one [here](https://www.cloudlab.us/signup.php) and ask the OSDI AEC chair to add you to the AEC project. Please let us know if you have trouble accessing CloudLab — we can help set up experiments and give you access.

### 1. Reserve Nodes

Machines may not always be available. To guarantee availability, click **Experiments → Reserve Nodes** from the CloudLab dashboard. Select the appropriate cluster and hardware type (see table above), specify the number of nodes and your desired time window, then submit the request. See [Resource Reservation](http://docs.cloudlab.us/reservations.html) for details.

> **Note:** A reservation does not automatically start an experiment.

### 2. Create Experiments Using Profiles

We provide three CloudLab profile XML files under `ae/cloudlab-profiles/`.

To use a profile:

1. Go to **Experiments → Create Experiment Profile**.
2. Click **Upload** and select the corresponding XML file (e.g., `xl170.xml`).
3. Give the profile a name and click **Create**.
4. Click **Instantiate** on the profile page, then keep clicking **Next** / **Finish**.
5. Wait for **Status** to become `Ready` on the experiment page.
6. Access each node via `ssh` using the hostname shown on the experiment page.

### 3. Install Xkernel
Please install Xkernel on **three** machines--c220g5, c6620 with IP 192.168.100.1, and xl170 with IP 192.168.6.1 before running the experiments. 

> **Note:** There is no need to install Xkernel on all c6620 and xl170 machines.

```bash
git clone https://github.com/zhongjiechen/Xkernel.git
cd Xkernel
./xkernel-tool setup # about 20-30minutes, depending on the machine.
export KERNEL_DIR=~/linux-6.8.0
```

## Experiment Structure

Each experiment directory (`ae/Figure*/`) follows a common three-script structure:

1. **`install_*.sh`** — Installs environment dependencies (benchmarks, libraries, etc.).
2. **`run.sh`** — Runs the experiment and saves raw data to `results/`.
3. **`plot/plot.py`** — Generates the corresponding figure from the paper.

Refer to the `README.md` inside each `Figure*/` directory for detailed instructions.

> **Note:** `run.sh` is designed to be **idempotent** (safe to re-run), though rare corner cases (e.g., unexpected interruption) may require manual cleanup before retrying.