# Adding a New Tunable to KernelX

This guide explains how to add a new kernel performance constant (perf-const)
to KernelX.

## Overview

To make a kernel constant tunable, you need to:
1. Identify the constant in the kernel source
2. Create a TOML config file
3. Build with the KernelX pipeline
4. (Optional) Write a tuning policy

## Step 1: Identify the Perf-Const

Find the constant in the Linux kernel source. Good candidates are:

- **Thresholds**: `#define MAX_SOFTIRQ_RESTART 10`
- **Batch sizes**: `#define BLK_MAX_REQUEST_COUNT 32`
- **Intervals/delays**: `#define BLK_MQ_RESOURCE_DELAY 3`
- **Scaling factors**: `ca->delay_min >> 3` (the `3` is the constant)

The constant must be a **numeric literal** used in performance-critical code.
It should NOT affect memory layout (array sizes, struct padding).

## Step 2: Choose Three Values

KernelX needs three values `(V1, V2, V3)`:
- **V1**: The original (default) value
- **V2**: A modified value
- **V3**: Another modified value, different from V1 and V2

These are used to understand how the compiler transforms the constant. Choose
values that produce different assembly (avoid powers of 2 if V1 is already a
power of 2, to get varied compiler optimizations).

**Good choices**: V1=128, V2=32, V3=64 — all different magnitudes.

## Step 3: Create TOML Config

### Single-tunable format

Create `tunables/my_const.toml`:

```toml
kernel_dir = "~/linux-6.8.0"

name = "MY_CONST"
description = "Brief description of what this controls"

[source]
file = "path/to/kernel/source.c"      # Relative to kernel root
original = "#define MY_CONST 128"      # sed pattern to find the line
modified = [
    "#define MY_CONST 32",             # V1 -> V2 replacement
    "#define MY_CONST 64",             # V1 -> V3 replacement
]
values = [128, 32, 64]                 # [V1, V2, V3]
```

### Adding to all.toml

For Linux 6.8-compatible tunables, you can also add to `tunables/all.toml` as
part of the multi-tunable array:

```toml
[[tunables]]
name = "MY_CONST"
description = "Brief description"
file = "path/to/source.c"
original = "#define MY_CONST 128"
modified = ["#define MY_CONST 32", "#define MY_CONST 64"]
values = [128, 32, 64]
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Unique identifier for the tunable |
| `description` | string | yes | Human-readable description |
| `file` | string | yes | Kernel source file path (relative to kernel root) |
| `original` | string | yes | sed search pattern (the line to replace) |
| `modified` | list[str] | yes | Exactly 2 replacement strings [V1→V2, V1→V3] |
| `values` | list[int] | yes | Exactly 3 values [V1, V2, V3] |
| `lines` | string | no | Optional `--lines` filter for gen.py |
| `safe_spans` | list | no | Safe Span ranges (see below) |

### Specifying Safe Spans

Safe Spans define where constant-derived values are still live. When omitted,
Critical Span (CS) ranges are used as a conservative approximation.

To specify Safe Spans, add `[[safe_spans]]` (for single format) or
`[[tunables.safe_spans]]` (for multi format):

```toml
[[tunables.safe_spans]]
function = "function_name"       # Kernel function containing the span
start_offset = "0x10"           # Hex offset from function start
end_offset = "0x90"             # Hex offset for span end
```

**Finding Safe Spans**: Two options.

* Compute them yourself by tracing forward data dependencies from the CS
  to where constant-derived values are last consumed (the LLVM thin-slicing
  approach described in the paper), and paste the results inline.
* Or run `./xkernel-tool build … --run-analysis` to invoke the LLVM
  taint pass automatically. See [`ss-analysis.md`](./ss-analysis.md) for
  details.

When `safe_spans` is left out and `--run-analysis` is not used, Xkernel
falls back to an auto-SS spanning the entire CS function (a conservative
over-approximation).

## Step 4: Build

```bash
# Build the new tunable
./xkernel-tool build tunables/my_const.toml

# Or with verbose output to see symbolic execution details
./xkernel-tool build tunables/my_const.toml --verbose
```

The pipeline will:
1. Recompile the kernel twice with V2 and V3
2. Diff the assembly to find seed instructions
3. Run symbolic execution to derive `IV = f(V)`
4. Generate a BPF kprobe stub
5. Compile the BPF program

## Step 5: Write a Policy (Optional)

The generated stub uses a fixed value. For dynamic policies:

```bash
# Generate a fresh stub
./xkernel-tool gen <ConstID> -o my_policy.bpf.c
```

Edit the policy to use runtime information:

```c
X_TUNE_0(my_function, "+0x1a3") {
    if (!x_transition_done(x_ctx)) return 0;

    // Example: set value based on CPU count
    u32 ncpus = bpf_get_num_possible_cpus();
    u64 val = (ncpus > 32) ? 64 : 128;
    x_set(x_ctx, val);
    return 0;
}
```

## Step 6: Load and Test

```bash
# Load in immediate mode
sudo ./xkernel-tool load 0 <ConstID>

# Check it's running
sudo ./xkernel-tool status

# Unload when done
sudo ./xkernel-tool unload <ConstID>
```

## Troubleshooting

- **"No diff found"**: The three values might produce identical assembly. Try
  values that are more different (e.g., different magnitudes).
- **"Symbolic execution failed"**: The compiler transformation might be too
  complex. Check `--verbose` output. The constant might involve non-linear
  transformations.
- **"kprobe registration failed"**: The target function might have multiple
  definitions (see Appendix C of the paper). Check `grep -c <func> /proc/kallsyms`.
