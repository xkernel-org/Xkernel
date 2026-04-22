# Figures 19 & 20

**Figure 19** — Deployment delay under varying trigger frequencies and thread counts. (a) Single-thread results; (b) Multi-thread (global convergence) results.

**Figure 20** — Global convergence overhead: delay and reference-count access across different thread counts and convergence levels.

These figures are **plot-only** — no experiment needs to be run. The underlying data comes from ad-hoc design drill-down measurements which conflicts with the code of current project structure.

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate
```

## Quick Start

```bash
cd ae/Figure19-20

# Generate Figure 19a (single-thread deployment delay)
cd single-thread
python plot_threads.py    # → threads-single.pdf

# Generate Figure 19b (multi-thread deployment delay)
cd multi-thread
python plot_threads.py    # → threads-global.pdf

# Generate Figure 20 (global convergence overhead)
python plot_global.py     # → global_converge.pdf
```

## Output

- `single-thread/threads-single.pdf` — Figure 19a: grouped bar chart showing deployment delay (ms) across four trigger-frequency/SS cases with 1, 4, and 16 threads (single-thread mode).
- `multi-thread/threads-global.pdf` — Figure 19b: grouped bar chart showing deployment delay (ms) across the same cases with 1, 4, and 16 threads (multi-thread/global mode).
- `multi-thread/global_converge.pdf` — Figure 20: two-panel bar chart showing global convergence delay (ms) and reference-count access counts across thread counts and convergence levels (log scale).
