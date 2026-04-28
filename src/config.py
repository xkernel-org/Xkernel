"""TOML config loader for tunable definitions.

Loads tunable configuration from TOML files and converts to
TunableConfig dataclass instances compatible with the codegen pipeline.

Supports two formats:
  1. Single-tunable file (top-level name/description/[source]/[[safe_spans]])
  2. Multi-tunable file ([[tunables]] array of tables)
"""

import os
import tomllib
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Kernel source directory resolution order:
#   1. KERNEL_DIR environment variable
#   2. kernel_dir field in the TOML config
#   3. Error if neither is set


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


def load_configs(path: str) -> Tuple[str, List[TunableConfig]]:
    """Load all tunables from a TOML config file.

    Supports two formats:
      1. Single: top-level name/description/[source] -> returns [TunableConfig]
      2. Multi:  [[tunables]] array -> returns list of TunableConfig

    Args:
        path: Path to the TOML config file.

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
        return kernel_dir, configs

    # Single-tunable format: top-level fields
    return kernel_dir, [_parse_tunable(data, path)]
