# Figure 15

**Figure 15** — CDF of instruction counts for functions, CSes, and SSes.

This figure compares the code size (in number of instructions) of whole
functions against CSes and SSes. It is **plot-only** — no experiment needs to be run.

Optionally refer to [linux-analysis](https://github.com/xkernel-org/linux-analysis)
repo on how to get SS statistics, namely `ss_instr_size.txt`.

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate
```

## Quick Start

```bash
cd ae/Figure15

# Generate Figure 15 (instruction size CDF)
python plot_func_instr_size.py    # → instr_compare.pdf
```

## Output

- `instr_compare.pdf` — Figure 15: CDF plot comparing the instruction count distributions of functions, CSes, and SSes on a log-scale x-axis.
