# Safe-Span (SS) Integration

This directory hooks the static SS analysis from the separate
[`linux-analysis`](https://github.com/xkernel-org/linux-analysis) project into
the Xkernel build pipeline.

## SS resolution order (per tunable)

`xkernel-tool build` resolves safe spans in this order, first match wins:

1. Inline `[[safe_spans]]` in the tunable's `*.toml` file.
2. Fresh LLVM analysis via `$WORKDIR/linux-analysis/scripts/ss-analysis.sh`,
   only when invoked with `--run-analysis`.
3. Auto-SS fallback in `codegen.py` (whole enclosing CS function, derived from
   `/proc/kcore`).

Steps (1)–(2) populate `TunableConfig.safe_spans`; step (3) only runs when
`safe_spans` is still `None`.

## Live LLVM analysis (`--run-analysis`)

Check out the
[linux-analysis](https://github.com/xkernel-org/linux-analysis) repo at
`$WORKDIR/linux-analysis`, follow its setup instructions to build the kernel
with `wllvm`, then:

```shell
./xkernel-tool build --run-analysis tunables/shrink_batch.toml
```

This invokes `$WORKDIR/linux-analysis/scripts/ss-analysis.sh` for each
`dataset/<NAME>/*.input.txt` file and feeds the results through
`ir_to_assembly.py` to recover assembly offsets. Results are written to
`*.output.txt` next to each input (cached on subsequent runs).

A few tunables in the dataset use ad-hoc directory names that don't match the
TOML `name` field (e.g. `tcp_min_rtt` ↔ `tcp_recovery`); the mapping lives in
`_dataset_to_toml_name` in `src/config.py`.

`linux-analysis` is intentionally kept as a **separate, untracked checkout** —
not a submodule — to keep that codebase's iteration independent of the main
project.
