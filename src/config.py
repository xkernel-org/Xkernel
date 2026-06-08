"""TOML config loader for tunable definitions.

Loads tunable configuration from TOML files and converts to
TunableConfig dataclass instances compatible with the codegen pipeline.

Supports two formats:
  1. Single-tunable file (top-level name/description/[source]/[[safe_spans]])
  2. Multi-tunable file ([[tunables]] array of tables)

Safe-span resolution order (per tunable, first match wins):
  1. Inline [[safe_spans]] in the TOML
  2. Fresh LLVM analysis via linux-analysis/scripts/ss-gen.sh
     (only when load_configs(..., run_analysis=True)).
     linux-analysis is located via the sibling-of-Xkernel convention
     (../linux-analysis relative to this repo root).

When both stages leave safe_spans=None, codegen.py's _populate_ss_raw()
falls back to an auto-SS spanning the entire CS function (kcore-derived).
"""

import glob
import json
import os
import subprocess
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
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
      2. LLVM analysis via linux-analysis/scripts/ss-gen.sh
         (only when run_analysis=True; linux-analysis is discovered via the
         sibling-of-Xkernel convention).

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


def _linux_analysis_root() -> Optional[Path]:
    """Locate the linux-analysis checkout via the sibling-of-Xkernel
    convention: <xkernel_parent>/linux-analysis.

    Returns the path if `scripts/ss-gen.sh` exists there, else None.
    """
    xkernel_root = Path(__file__).resolve().parents[1]
    candidate = xkernel_root.parent / "linux-analysis"
    if (candidate / "scripts" / "ss-gen.sh").is_file():
        return candidate
    return None


def _backfill_safe_spans_from_analysis(
    configs: List[TunableConfig],
) -> List[TunableConfig]:
    """Run LLVM SS analysis (linux-analysis) for tunables missing safe_spans.

    Discovers linux-analysis as a sibling directory of Xkernel
    (../linux-analysis), then for each tunable without inline safe_spans
    invokes `scripts/ss-gen.sh --tunable <NAME>` and reads the resulting
    dataset/<NAME>/*.func_offset.json files. Existing JSON outputs are
    reused (ss-gen.sh caches *.output.txt + *.func_offset.json on disk).
    """
    if all(c.safe_spans is not None for c in configs):
        return configs

    la_root = _linux_analysis_root()
    if la_root is None:
        xkernel_root = Path(__file__).resolve().parents[1]
        print(
            f"  --run-analysis: no linux-analysis checkout at "
            f"{xkernel_root.parent / 'linux-analysis'}, skipping. "
            "Clone xkernel-org/linux-analysis as a sibling of Xkernel to enable."
        )
        return configs

    ss_gen_script = la_root / "scripts" / "ss-gen.sh"
    dataset_dir = la_root / "dataset"

    # Optional flags forwarded to ss-gen.sh. Empty strings are dropped so the
    # underlying script uses its own defaults (env vars / self-relative paths).
    forwarded: List[str] = []
    for flag, var in (
        ("--linux-wllvm", "LINUX_WLLVM"),
        ("--vmlinux-bc",  "VMLINUX_BC"),
        ("--plugin",      "TAINT_TRACKER_PLUGIN"),
        ("--vmlinux",     "VMLINUX"),
        ("--modules-dir", "MODULES_DIR"),
    ):
        val = os.environ.get(var)
        if val:
            forwarded += [flag, val]

    resolved = []
    for config in configs:
        if config.safe_spans is not None:
            resolved.append(config)
            continue

        ds_name = _toml_to_dataset_name.get(config.name, config.name)
        tunable_dir = dataset_dir / ds_name
        if not tunable_dir.is_dir():
            print(f"  {config.name}: no dataset at {tunable_dir}, skipping --run-analysis")
            resolved.append(config)
            continue

        print(f"  {config.name}: invoking ss-gen.sh --tunable {ds_name}")
        result = subprocess.run(
            ["bash", str(ss_gen_script), "--tunable", ds_name, *forwarded],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(f"  {config.name}: ss-gen.sh failed (exit {result.returncode})")
            resolved.append(config)
            continue

        all_spans: List[Tuple[str, str, str]] = []
        seen: set = set()
        for json_file in sorted(tunable_dir.glob("*.func_offset.json")):
            for span in _parse_func_offset_json(json_file):
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


def _parse_func_offset_json(path: Path) -> List[Tuple[str, str, str]]:
    """Convert a *.func_offset.json file from linux-analysis into
    (function, start_offset, end_offset) tuples. The `offset` field has
    the form `"0xNN - 0xMM"`.
    """
    try:
        entries = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print(f"    warning: cannot read {path}: {e}")
        return []

    spans: List[Tuple[str, str, str]] = []
    for entry in entries:
        func = entry.get("function")
        offset = entry.get("offset", "")
        if not func or " - " not in offset:
            continue
        soff, eoff = (s.strip() for s in offset.split(" - ", 1))
        if int(soff, 16) >= int(eoff, 16):
            soff, eoff = eoff, soff
        spans.append((func, soff, eoff))
    return spans
