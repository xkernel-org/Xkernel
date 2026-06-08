# Safe Span (SS) analysis

This document describes how Xkernel obtains Safe Span ranges for each
tunable, and the optional integration with the LLVM-based taint analysis
in the [`linux-analysis`](https://github.com/xkernel-org/linux-analysis)
repository.

## What is a Safe Span?

A **Safe Span (SS)** is the forward data-dependency slice rooted at a
Critical Span (CS). It covers every instruction window in which a value
derived from the perf-const is still live in architectural state. The
consistency model uses SS ranges to decide whether a thread is currently
inside a region that observes the old constant: a transition is safe
only when execution is outside *all* SSes.

For background, see Sections 4–5 of the
[paper](https://arxiv.org/abs/2512.12530).

## Resolution order

For every tunable, Xkernel resolves its SS using the first source that
matches:

1. **Inline `[[safe_spans]]` in the TOML.** The author has already
   computed the spans (manually or via a prior analysis run) and pasted
   them into the config. See [adding-a-tunable.md](./adding-a-tunable.md).

2. **Fresh LLVM analysis** (only when invoked with `--run-analysis`).
   Xkernel calls into a sibling `linux-analysis` checkout and reads the
   generated `*.func_offset.json`. See below.

3. **Auto-SS** (fallback). When neither of the above produces a span,
   `codegen.py:_populate_ss_raw()` synthesises a single SS that covers
   the entire CS function (extents derived from `/proc/kcore`). This is
   a conservative over-approximation: every instruction in the function
   is treated as observing the constant.

If `--run-analysis` is *not* passed, step 2 is skipped entirely and the
pipeline goes straight from step 1 to step 3. This is the path taken by
the 30-Second Demo in the top-level `README.md`.

## Stage 2: invoking `linux-analysis`

When you pass `--run-analysis` to `xkernel-tool build`:

```bash
./xkernel-tool build tunables/my_const.toml --run-analysis
```

`src/config.py:_backfill_safe_spans_from_analysis` runs for every
tunable that lacks inline `safe_spans`:

1. Locate the `linux-analysis` checkout.
2. For each such tunable, invoke
   `bash <linux-analysis>/scripts/ss-gen.sh --tunable <NAME>`.
   `ss-gen.sh` runs the LLVM taint pass on the wllvm-built kernel
   bitcode, then translates the resulting IR locations into assembly
   offsets via `objdump`.
3. Read every `dataset/<NAME>/*.func_offset.json` file and convert each
   entry into a `(function, start_offset, end_offset)` tuple. The
   `offset` field has the form `"0xNN - 0xMM"` and is split on `" - "`.
4. Deduplicate and splice the result into the `TunableConfig` as
   `safe_spans`.

If anything in this stage fails (missing checkout, `ss-gen.sh` non-zero
exit, no JSON produced) Xkernel prints a diagnostic and falls through to
auto-SS. `--run-analysis` is therefore best-effort: it is never a hard
build dependency.

### Locating `linux-analysis`

`_linux_analysis_root()` checks two paths in order and returns the first
that contains `scripts/ss-gen.sh`:

1. **Sibling-of-Xkernel** (preferred): `<xkernel_parent>/linux-analysis`
2. **In-tree** (development convenience): `<xkernel_root>/linux-analysis`

If neither exists, `--run-analysis` prints a diagnostic and the
pipeline falls back to auto-SS.

### Optional environment variables

Xkernel forwards the following environment variables to `ss-gen.sh` as
flags when set; otherwise `ss-gen.sh`'s self-relative defaults apply.
None are required for normal use.

| Env var                | `ss-gen.sh` flag        | Default                                                    |
|------------------------|-------------------------|------------------------------------------------------------|
| `LINUX_WLLVM`          | `--linux-wllvm DIR`     | `$LINUX_WLLVM`                                             |
| `VMLINUX_BC`           | `--vmlinux-bc PATH`     | `<linux-wllvm>/vmlinux-xk-dataset.bc`                      |
| `TAINT_TRACKER_PLUGIN` | `--plugin PATH`         | `<linux-analysis>/passes/build/libTaintTrackerPass.so`     |
| `VMLINUX`              | `--vmlinux PATH`        | `$VMLINUX`, `$LINUX_GCC/vmlinux`, `~/linux-6.8.0/vmlinux`  |
| `MODULES_DIR`          | `--modules-dir PATH`    | `/lib/modules/$(uname -r)`                                 |

A typical invocation in a freshly-set-up environment looks like:

```bash
export LINUX_WLLVM=~/linux-analysis-workdir/linux-6.8.0-wllvm
./xkernel-tool build tunables/my_const.toml --run-analysis
```

## Caching

`ss-gen.sh` writes (and reuses) two files per input:

* `dataset/<NAME>/<N>.output.txt` — raw IR-level taint output (stage 1).
* `dataset/<NAME>/<N>.func_offset.json` — assembly-offset-translated
  result (stage 2). This is the file Xkernel actually consumes.

Re-running `--run-analysis` on a tunable whose dataset is already
populated is therefore cheap: `ss-gen.sh` re-emits the same JSON
deterministically and Xkernel simply re-parses it.

To force a re-analysis, delete the relevant `*.output.txt` and
`*.func_offset.json` files in the dataset.

## Adding a tunable to the analysis dataset

Each `dataset/<NAME>/<N>.input.txt` is a small shell-style file pinning
one occurrence of the constant for the taint pass:

```
SOURCE_FILE=block/blk-core.c
FUNCTION_NAME=blk_start_plug_nr_ios
SOURCE_OP="call"
CONSTANT_VALUE=32
OCCURENCE=1
```

`linux-analysis/dataset/source-occurrence-and-mutation.sh` is the
canonical generator that derives these from a TOML mutation list. See
the [`linux-analysis` README](../linux-analysis/README.md) for the
full workflow.

## Known stragglers

A small number of tunables currently time out the LLVM pass on 6.8 IR
(>55 minutes). These are documented in
[`linux-analysis/dataset/UNSUCCESSFUL.md`](../linux-analysis/dataset/UNSUCCESSFUL.md)
and gracefully fall back to auto-SS when `--run-analysis` is requested.
