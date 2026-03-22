"""TOML config loader for tunable definitions.

Loads tunable configuration from TOML files and converts to
TunableConfig dataclass instances compatible with the codegen pipeline.

Supports two formats:
  1. Single-tunable file (top-level name/description/[source]/[[safe_spans]])
  2. Multi-tunable file ([[tunables]] array of tables)

Safe-span resolution order (per tunable):
  1. Manually specified safe_spans in the TOML
  2. CSV lookup by tunable name

"""

import csv
import os
import tomllib
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

DEFAULT_KERNEL_DIR = "~/linux-6.14.0-xkernel"
DEFAULT_SAFE_SPANS_CSV = "ss/ss-addresses.csv"


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


def load_safe_spans_csv(csv_path: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """Load safe-span definitions from ss-addresses.csv.

    Expected format (header required):
        ID,directory,file,function,offset,source start,source end
        40,SHRINK_BATCH,...,__pfx_perf_trace_mm_shrink_slab_end,0x15145 - 0x10,...

    The 'directory' column is used as the tunable name for lookup.
    The 'offset' column contains "0xSTART - 0xEND".

    Rows with identical (directory, function, start_offset, end_offset) are
    deduplicated.

    Returns:
        Dict mapping tunable name -> [(function, start_offset, end_offset), ...]
    """
    spans_by_name: Dict[str, List[Tuple[str, str, str]]] = {}

    # For PerfConsts that are not a macro (thus do not have a clear identifier)
    # we are coming up with ad-hoc names. This translates the name in dataset
    # to the ones used in TOML.
    name_translate = {
        'tcp_min_rtt': 'tcp_recovery',
        'ca__delay_min': 'tcp_cubic',
    }

    if not os.path.exists(csv_path):
        return spans_by_name

    seen: set = set()

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        required = {'directory', 'function', 'offset'}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            print(f"Error: CSV {csv_path} missing required columns {required}, "
                  f"found {reader.fieldnames}")
            exit(1)

        for row in reader:
            name = row['directory'].strip()
            if name in name_translate:
                name = name_translate[name]
            func = row['function'].strip()
            offset_raw = row['offset'].strip()

            if not name or not func or not offset_raw:
                print("Error: malformed CSV entry: {row}")
                exit(1)

            parts = offset_raw.split(' - ')
            if len(parts) != 2:
                print("Error: malformed CSV entry: {row}")
                exit(1)
            soff = parts[0].strip()
            eoff = parts[1].strip()

            if int(soff, 16) >= int(eoff, 16):
                swap = soff
                soff = eoff
                eoff = swap

            key = (name, func, soff, eoff)
            if key in seen:
                continue
            seen.add(key)

            spans_by_name.setdefault(name, []).append((func, soff, eoff))

    return spans_by_name


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


def load_configs(path: str) -> Tuple[str, List[TunableConfig]]:
    """Load all tunables from a TOML config file.

    Supports two formats:
      1. Single: top-level name/description/[source] -> returns [TunableConfig]
      2. Multi:  [[tunables]] array -> returns list of TunableConfig

    For tunables without inline [[safe_spans]], attempts CSV lookup by name
    from ss/dataset.csv.

    Args:
        path: Path to the TOML config file.

    Returns:
        (kernel_dir, list_of_TunableConfig) tuple.
    """
    with open(path, 'rb') as f:
        data = tomllib.load(f)

    kernel_dir = os.path.expanduser(data.get('kernel_dir', DEFAULT_KERNEL_DIR))

    # Multi-tunable format: [[tunables]] array
    if 'tunables' in data:
        configs = []
        for i, entry in enumerate(data['tunables']):
            configs.append(_parse_tunable(entry, f"{path} tunables[{i}]"))
    else:
        # Single-tunable format: top-level fields
        configs = [_parse_tunable(data, path)]

    # Resolve safe_spans from CSV for tunables that don't have inline spans
    configs = _backfill_safe_spans_from_csv(configs, path)

    return kernel_dir, configs


def _backfill_safe_spans_from_csv(
    configs: List[TunableConfig],
    toml_path: str,
) -> List[TunableConfig]:
    """Fill in missing safe_spans from a CSV file.

    Only tunables with safe_spans=None are updated. Tunables that already
    have inline [[safe_spans]] are left untouched.
    """
    needs_lookup = any(c.safe_spans is None for c in configs)
    if not needs_lookup:
        return configs

    csv_path = DEFAULT_SAFE_SPANS_CSV
    csv_spans = load_safe_spans_csv(csv_path)
    if not csv_spans:
        return configs

    resolved = []
    for config in configs:
        if config.safe_spans is None and config.name in csv_spans:
            spans = csv_spans[config.name]
            config = replace(config, safe_spans=spans)
            print(f"  {config.name}: resolved {len(spans)} safe_span(s) from {csv_path}")
            print(f"  {config.name}: {spans}")
        resolved.append(config)

    return resolved
