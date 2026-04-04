# KernelX Quickstart Guide

This guide walks you through tuning a kernel constant end-to-end in under 30 minutes.

## Prerequisites

1. **Custom kernel installed and booted** (`6.14.0-xkernel`):
   ```bash
   sudo bash install.sh
   # Reboot into the new kernel
   ```

2. **Dependencies built**:
   ```bash
   sudo bash build.sh
   ```

3. **Verify everything**:
   ```bash
   ./xkernel-tool doctor
   ```

## Step 1: Pick a Tunable

We'll use `SHRINK_BATCH`, which controls how many entries the memory shrinker
processes per scan. The default value (128) has been unchanged since 2005.

The config is already defined in `tunables/shrink_batch.toml`:

```toml
name = "SHRINK_BATCH"
description = "mm/shrinker.c SHRINK_BATCH"

[source]
file = "mm/shrinker.c"
original = "#define SHRINK_BATCH 128"
modified = ["#define SHRINK_BATCH 32", "#define SHRINK_BATCH 64"]
values = [128, 32, 64]
```

The three values (128, 32, 64) are used by the pipeline to understand how the
compiler transforms the constant.

## Step 2: Build

```bash
./xkernel-tool build tunables/shrink_batch.toml
```

This runs the full pipeline:
1. **gen.py** — Recompiles the kernel twice (V1→V2 and V1→V3), diffs the
   assembly, extracts Basic Blocks
2. **codegen.py** — Symbolic execution on the BBs to derive `IV = f(V)`,
   generates BPF kprobe stub
3. **make** — Compiles the BPF program

Output:
```
Build completed: 1 tunable(s)
  SHRINK_BATCH -> ConstID 1
```

> **Tip**: If you've already built once, skip the slow diff step:
> `./xkernel-tool build tunables/shrink_batch.toml --skip-gen`

## Step 3: Inspect the Generated Stub

Look at the generated policy file:

```bash
cat bpf/stubs/xtune_stub_1.bpf.c
```

You'll see something like:
```c
X_TUNE_0(do_shrink_slab, "+0x1a3") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 128; // original value
    x_set(x_ctx, val);
    return 0;
}
```

Edit this to set your desired value (e.g., change `128` to `32`).

## Step 4: Load

```bash
# Immediate mode (takes effect instantly)
sudo ./xkernel-tool load 0 1
```

The tool will:
- Load the kernel module `xk-kfuncs.ko` (if not already loaded)
- Attach the BPF kprobe at the Critical Span location
- Print a summary of loaded kprobes

## Step 5: Verify

```bash
# Check status
sudo ./xkernel-tool status

# View scope table
./xkernel-tool table list
```

## Step 6: Unload

```bash
sudo ./xkernel-tool unload 1
```

## Next Steps

- **Write a policy**: Instead of a fixed value, write eBPF logic that decides
  the value dynamically. See `examples/policy/` for samples.
- **Add a new tunable**: See `docs/adding-a-tunable.md`.
- **Try consistency modes**: Use mode 1 (per-task) or mode 2 (global) for
  safe transitions under concurrent workloads.
- **Run experiments**: See `ae/README.md` for reproducing paper figures.
