# Figure 17

**Figure 17** — Latency breakdown of the BPF-to-kprobe deployment pipeline (BPF verification, JMP optimization, kprobe registration) across three design-drill-down cases: 1 SS best, 1 SS worst, and 15 SS worst.

This figure is **plot-only** — no experiment needs to be run. The underlying data comes from ad-hoc design drill-down measurements which conflicts with the code of current project structure.
## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate
```

## Quick Start

```bash
cd ae/Figure17

# Generate Figure 17 (latency breakdown bar chart)
python plot_policy.py    # → timeline_latency_bar.pdf
```

## Output

- `timeline_latency_bar.pdf` — Figure 17: grouped bar chart showing latency (ms) for BPF verify, JMP optimization, kprobe registration, and their sum across three deployment cases. The rightmost two panels use a log scale.
