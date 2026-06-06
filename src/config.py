"""TOML config loader for tunable definitions.

Loads tunable configuration from TOML files and converts to
TunableConfig dataclass instances compatible with the codegen pipeline.

Supports two formats:
  1. Single-tunable file (top-level name/description/[source]/[[safe_spans]])
  2. Multi-tunable file ([[tunables]] array of tables)

Safe-span resolution order (per tunable, first match wins):
  1. Inline [[safe_spans]] in the TOML
  2. Fresh LLVM analysis via linux-analysis/scripts/ss-analysis.sh
     (only when load_configs(..., run_analysis=True))

When both stages leave safe_spans=None, codegen.py's _populate_ss_raw()
falls back to an auto-SS spanning the entire CS function (kcore-derived).
"""

import glob
import os
import subprocess
import tomllib
from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

# Kernel source directory resolution order:
#   1. KERNEL_DIR environment variable
#   2. kernel_dir field in the TOML config
#   3. Error if neither is set

# A few tunables in the linux-analysis dataset use ad-hoc names because the
# perf-const is not a single macro/identifier. This translates the dataset
# directory name to the TOML `name` used in xkernel.
_dataset_to_toml_name = {
    'tcp_min_rtt': 'tcp_recovery',
    'ca__delay_min': 'tcp_cubic',
}
_toml_to_dataset_name = {v: k for k, v in _dataset_to_toml_name.items()}


@dataclass(frozen=True)
class TunableConfig:
    """Configuration for a single kernel tunable constant."""
    name: str
    description: str
    file: str           # kernel source file (e.g. "mm/shrinker.c")
    original: str       # sed search pattern (original expression)
    modified: list      # [V1->V2 replacement, V1->V3 replacement]
    values: tuple       # (V1, V2, V3)
    lines: str = None   # optional --lines filter
    safe_spans: list = None  # [(func_name, "0xNN", "0xMM"), ...]


def _parse_tunable(data: dict, context: str) -> TunableConfig:
    """Parse a single tunable entry from a dict.

    Args:
        data: Dictionary with tunable fields.
        context: Description string for error messages (e.g. file path or index).
    """
    for field in ('name', 'description'):
        if field not in data:
            raise ValueError(f"Missing required field: '{field}' in {context}")

    # Source fields can be in a [source] sub-table or at the top level
    source = data.get('source', data)

    for field in ('file', 'original', 'modified', 'values'):
        if field not in source:
            raise ValueError(f"Missing required field: '{field}' in {context}")

    modified = source['modified']
    if not isinstance(modified, list) or len(modified) != 2:
        raise ValueError(f"'modified' must be a list of exactly 2 strings in {context}")

    values = source['values']
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"'values' must be a list of exactly 3 integers in {context}")
    values = tuple(values)

    lines = source.get('lines') or None

    # Parse safe_spans
    safe_spans = None
    raw_spans = data.get('safe_spans')
    if raw_spans:
        safe_spans = []
        for span in raw_spans:
            func = span.get('function')
            soff = span.get('start_offset')
            eoff = span.get('end_offset')
            if not all([func, soff, eoff]):
                raise ValueError(
                    f"Each safe_spans entry must have 'function', "
                    f"'start_offset', 'end_offset' in {context}"
                )
            safe_spans.append((func, soff, eoff))

    return TunableConfig(
        name=data['name'],
        description=data['description'],
        file=source['file'],
        original=source['original'],
        modified=modified,
        values=values,
        lines=lines,
        safe_spans=safe_spans,
    )


def load_config(path: str) -> Tuple[str, TunableConfig]:
    """Load a single-tunable TOML config file.

    For multi-tunable files, use load_configs() instead.
    If the file contains [[tunables]], returns the first one.

    Returns:
        (kernel_dir, TunableConfig) tuple.
    """
    kernel_dir, configs = load_configs(path)
    if not configs:
        raise ValueError(f"No tunables found in {path}")
    return kernel_dir, configs[0]


def load_configs(path: str, *, run_analysis: bool = False) -> Tuple[str, List[TunableConfig]]:
    """Load all tunables from a TOML config file.

    Supports two formats:
      1. Single: top-level name/description/[source] -> returns [TunableConfig]
      2. Multi:  [[tunables]] array -> returns list of TunableConfig

    Safe-span resolution (per tunable, first match wins):
      1. Inline [[safe_spans]] in the TOML
      2. LLVM analysis via linux-analysis/scripts/ss-analysis.sh
         (only when run_analysis=True)

    Args:
        path: Path to the TOML config file.
        run_analysis: If True, run the LLVM SS analysis for tunables that
            do not already have inline safe_spans.

    Returns:
        (kernel_dir, list_of_TunableConfig) tuple.
    """
    with open(path, 'rb') as f:
        data = tomllib.load(f)

    # Resolve kernel source directory: env var > TOML field > error
    env_kernel_dir = os.environ.get('KERNEL_DIR')
    toml_kernel_dir = data.get('kernel_dir')
    if env_kernel_dir:
        kernel_dir = os.path.expanduser(env_kernel_dir)
    elif toml_kernel_dir:
        kernel_dir = os.path.expanduser(toml_kernel_dir)
    else:
        raise ValueError(
            f"Kernel source directory not specified.\n"
            f"Set the KERNEL_DIR environment variable:\n"
            f"  export KERNEL_DIR=~/linux-6.8.0\n"
            f"Or add 'kernel_dir = \"~/linux-6.8.0\"' to {path}"
        )

    # Multi-tunable format: [[tunables]] array
    if 'tunables' in data:
        configs = []
        for i, entry in enumerate(data['tunables']):
            configs.append(_parse_tunable(entry, f"{path} tunables[{i}]"))
    else:
        # Single-tunable format: top-level fields
        configs = [_parse_tunable(data, path)]

    # Optional fresh LLVM analysis for tunables without inline safe_spans
    if run_analysis:
        configs = _backfill_safe_spans_from_analysis(configs)

    return kernel_dir, configs


# ---------------------------------------------------------------------------
# Safe-span backfill via linux-analysis (--run-analysis)
# ---------------------------------------------------------------------------


def _backfill_safe_spans_from_analysis(
    configs: List[TunableConfig],
) -> List[TunableConfig]:
    """Run LLVM SS analysis (linux-analysis) for tunables missing safe_spans.

    Looks for input files at $WORKDIR/linux-analysis/dataset/<name>/*.input.txt
    and runs ss-analysis.sh on each, then ir_to_assembly.py to recover
    assembly offsets. Results are deduplicated and stored in TunableConfig.
    """
    if all(c.safe_spans is not None for c in configs):
        return configs

    workdir = os.environ.get('WORKDIR')
    if not workdir:
        raise RuntimeError(
            "WORKDIR environment variable is not set. "
            "Set it to the parent directory containing the linux-analysis checkout, e.g.:\n"
            "  export WORKDIR=~"
        )

    base = os.path.join(workdir, "linux-analysis")
    ss_analysis_script = os.path.join(base, "scripts", "ss-analysis.sh")
    ir_to_assembly_script = os.path.join(base, "scripts", "ir_to_assembly.py")
    dataset_dir = os.path.join(base, "dataset")

    for required in (ss_analysis_script, ir_to_assembly_script):
        if not os.path.isfile(required):
            raise FileNotFoundError(
                f"linux-analysis script not found: {required}\n"
                f"Check out https://github.com/xkernel-org/linux-analysis at $WORKDIR/linux-analysis."
            )

    resolved = []
    for config in configs:
        if config.safe_spans is not None:
            resolved.append(config)
            continue

        ds_name = _toml_to_dataset_name.get(config.name, config.name)
        tunable_dir = os.path.join(dataset_dir, ds_name)
        if not os.path.isdir(tunable_dir):
            print(f"  {config.name}: no dataset at {tunable_dir}, skipping --run-analysis")
            resolved.append(config)
            continue

        input_files = sorted(glob.glob(os.path.join(tunable_dir, "*.input.txt")))
        if not input_files:
            print(f"  {config.name}: no input files in {tunable_dir}, skipping --run-analysis")
            resolved.append(config)
            continue

        print(f"  {config.name}: running analysis on {len(input_files)} input file(s)...")
        all_spans: List[Tuple[str, str, str]] = []
        seen: set = set()
        for input_file in input_files:
            spans = _run_ss_analysis(ss_analysis_script, ir_to_assembly_script, input_file)
            for span in spans or []:
                if span not in seen:
                    seen.add(span)
                    all_spans.append(span)

        if all_spans:
            config = replace(config, safe_spans=all_spans)
            print(f"  {config.name}: analysis produced {len(all_spans)} span(s)")
        else:
            print(f"  {config.name}: analysis produced no spans")

        resolved.append(config)

    return resolved


def _run_ss_analysis(
    ss_analysis_script: str, ir_to_assembly_script: str, input_file: str,
) -> List[Tuple[str, str, str]]:
    """Run ss-analysis.sh on one input file (with output caching), then
    ir_to_assembly.py to translate IR locations to assembly offsets.

    The .output.txt file is cached next to the .input.txt so re-runs are fast.
    """
    output_file = input_file.replace(".input.txt", ".output.txt")

    if not os.path.exists(output_file):
        print(f"    Running: bash {ss_analysis_script} {input_file}")
        result = subprocess.run(
            ["bash", ss_analysis_script, input_file],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        with open(output_file, "w") as f:
            f.write(result.stdout)
    else:
        print(f"    Cached: {output_file}")

    return _parse_analysis_output(ir_to_assembly_script, output_file)


def _parse_analysis_output(
    ir_to_assembly_script: str, output_file: str,
) -> List[Tuple[str, str, str]]:
    """Run ir_to_assembly.py and parse its 'SPAN, ...' stdout lines."""
    print(f"    Running: python3 {ir_to_assembly_script} {output_file}")
    result = subprocess.run(
        ["python3", ir_to_assembly_script, output_file],
        capture_output=True, text=True,
    )

    spans: List[Tuple[str, str, str]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("SPAN, "):
            continue
        # SPAN, source_start, source_end, abs_start, abs_end, func, start_off, end_off
        parts = [p.strip() for p in line.split(", ")]
        if len(parts) == 8:
            func, soff, eoff = parts[5], parts[6], parts[7]
            if int(soff, 16) >= int(eoff, 16):
                soff, eoff = eoff, soff
            spans.append((func, soff, eoff))

    return spans
