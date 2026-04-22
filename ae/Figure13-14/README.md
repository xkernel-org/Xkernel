# Figure 13 & 14

**Figure 13** — Distribution of perf-consts across kernel subsystems and by source form / semantic category.

**Figure 14** — Distribution of the number of CS and SS per perf-const.

These figures characterize the dataset of perf-consts identified in the Linux
kernel. They are **plot-only** — no experiment needs to be run.

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate
```

## Quick Start

```bash
cd ae/Figure13-14

# Generate Figure 13 (dataset distribution)
python plot_dataset.py          # → dataset_distribution.pdf

# Generate Figure 14 (CS & SS number distribution)
python plot_cs_number.py        # → cs_number_dist.pdf
```

## Output

- `dataset_distribution.pdf` — Figure 13: a 3-panel subplot showing (a)
  subsystem distribution (with block+io+fs merged into "storage"), (b) source
  form, and (c) semantic category.
- `cs_number_dist.pdf` — Figure 14: grouped bar chart of CS and SS number
  distributions.
