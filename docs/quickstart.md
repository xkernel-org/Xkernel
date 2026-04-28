# KernelX Quickstart Guide

This guide walks you through tuning a kernel constant end-to-end in under 30 minutes.

## Prerequisites

1. **Linux 6.8 kernel source prepared**:
   ```bash
   export KERNEL_DIR=~/linux-6.8.0
   ```

2. **Dependencies built**:
   ```bash
   ./xkernel-tool setup
   ```

3. **Verify everything**:
   ```bash
   ./xkernel-tool doctor
   ```

## Step 1: Pick a Tunable

We'll use `BLK_MAX_REQUEST_COUNT`, which controls how many block I/O requests
can be batched together before dispatch.

The config is already defined in `tunables/blk_max_request_count.toml`:

```toml
kernel_dir = "~/linux-6.8.0"

name = "BLK_MAX_REQUEST_COUNT"
description = "block/blk-mq.c BLK_MAX_REQUEST_COUNT"

[source]
file = "block/blk-mq.c"
original = "BLK_MAX_REQUEST_COUNT"
modified = ["8", "16"]
values = [32, 8, 16]
```

The three values (32, 8, 16) are used by the pipeline to understand how the
compiler transforms the constant.

## Step 2: Build

```bash
./xkernel-tool build tunables/blk_max_request_count.toml
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
  BLK_MAX_REQUEST_COUNT -> ConstID 1
```

> **Tip**: If you've already built once, skip the slow diff step:
> `./xkernel-tool build tunables/blk_max_request_count.toml --skip-gen`

## Step 3: Inspect the Generated Stub

Look at the generated policy file:

```bash
cat bpf/stubs/xtune_stub_1.bpf.c
```

You'll see something like:
```c
X_TUNE_0(blk_add_rq_to_plug, "+0x1a3") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 32; // original value
    x_set(x_ctx, val);
    return 0;
}
```

Edit this to set your desired value (e.g., change `32` to `8`).

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
