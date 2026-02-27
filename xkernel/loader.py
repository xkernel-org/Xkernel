#!/usr/bin/env python3
"""BPF program loader for Xkernel.

Replaces the C++ kprobe_loader with Python + bpftool.
Handles:
  - cs_artifact.bpf.h generation
  - BPF program compilation
  - BPF program loading/attaching/pinning via bpftool
  - Critical span map population
"""

import json
import os
import re
import struct
import subprocess
import sys
import time


CS_PATH = "/dev/shm/xkernel/cs"
RUNTIME_STATE_PATH = "/dev/shm/xkernel/runtime_state"
BPF_PIN_BASE = "/sys/fs/bpf/xkernel"


def generate_cs_artifact_header(spans_path, output_path):
    """Generate cs_artifact.bpf.h with guard/unguard kprobe pairs from span ranges.

    Guard kprobe at SS entry (soff): per-task stack check / global refcount++
    Unguard kprobe at SS exit (eoff): global refcount--

    Args:
        spans_path: Path to spans file (format: function_name,address,soff,eoff per line)
        output_path: Path to write the BPF header
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    empty_header = (
        "// Empty cs_artifact.bpf.h - no spans defined\n"
        "#ifndef __CS_ARTIFACT_BPF_H__\n"
        "#define __CS_ARTIFACT_BPF_H__\n"
        "#endif\n"
    )

    if not os.path.exists(spans_path):
        with open(output_path, 'w') as f:
            f.write(empty_header)
        print(f"Spans file {spans_path} does not exist, created empty {output_path}",
              file=sys.stderr)
        return

    with open(spans_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        with open(output_path, 'w') as f:
            f.write(empty_header)
        print(f"Spans file {spans_path} is empty, created empty {output_path}",
              file=sys.stderr)
        return

    # Parse span entries: funcname,0xaddr,soff,eoff
    span_entries = []
    for line in lines:
        parts = line.split(',')
        if len(parts) < 4:
            print(f"Malformed line in {spans_path}: {line}", file=sys.stderr)
            continue
        func_name = parts[0]
        soff = int(parts[2], 16)
        eoff = int(parts[3], 16)
        span_entries.append((func_name, soff, eoff))

    # Generate BPF header with guard/unguard pairs
    with open(output_path, 'w') as f:
        f.write("#ifndef __CS_ARTIFACT_BPF_H__\n")
        f.write("#define __CS_ARTIFACT_BPF_H__\n\n")
        f.write('#include "xkernel.bpf.h"\n\n')

        for func_name, soff, eoff in span_entries:
            # Guard kprobe at SS entry (soff)
            guard_sec = f"kprobe/{func_name}+0x{soff:x}" if soff else f"kprobe/{func_name}"
            guard_fn = f"__xk_guard_{func_name}_{soff:x}"
            f.write(f'// Guard: {func_name}+0x{soff:x} (SS entry)\n')
            f.write(f'SEC("{guard_sec}")\n')
            f.write(f'int BPF_KPROBE({guard_fn}) {{\n')
            f.write('    ss_guard_handler(ctx);\n')
            f.write('    return 0;\n')
            f.write('}\n\n')

            # Unguard kprobe at SS exit (eoff)
            unguard_sec = f"kprobe/{func_name}+0x{eoff:x}" if eoff else f"kprobe/{func_name}"
            unguard_fn = f"__xk_unguard_{func_name}_{eoff:x}"
            f.write(f'// Unguard: {func_name}+0x{eoff:x} (SS exit)\n')
            f.write(f'SEC("{unguard_sec}")\n')
            f.write(f'int BPF_KPROBE({unguard_fn}) {{\n')
            f.write('    ss_unguard_handler(ctx);\n')
            f.write('    return 0;\n')
            f.write('}\n\n')

        f.write("#endif\n")

    file_size = os.path.getsize(output_path)
    print(f"Generated {output_path} ({file_size} bytes, {len(span_entries)} guard/unguard pairs)",
          file=sys.stderr)


def compile_bpf_programs(bpf_dir):
    """Compile all BPF programs in the examples directory.

    Args:
        bpf_dir: Path to the bpf/ directory
    """
    examples_dir = os.path.join(bpf_dir, 'examples')
    if not os.path.isdir(examples_dir):
        print(f"Examples directory not found: {examples_dir}", file=sys.stderr)
        return False

    print(f"Compiling BPF files in {examples_dir}...", file=sys.stderr)
    success = True
    for fname in sorted(os.listdir(examples_dir)):
        if not fname.endswith('.bpf.c'):
            continue
        src = os.path.join(examples_dir, fname)
        obj = src[:-2] + '.o'  # .bpf.c -> .bpf.o
        cmd = [
            'clang', '-g', '-O2', '-target', 'bpf',
            '-D__TARGET_ARCH_x86',
            f'-I{bpf_dir}',
            '-I/usr/include/bpf',
            '-c', src, '-o', obj,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: Failed to compile {fname}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            success = False
        else:
            print(f"Compiled: {fname} -> {os.path.basename(obj)}", file=sys.stderr)

    print("BPF compilation completed", file=sys.stderr)
    return success


def load_and_attach(bpf_files, pin=True):
    """Load and attach BPF programs using bpftool.

    Args:
        bpf_files: List of .bpf.o file paths
        pin: Whether to pin programs to /sys/fs/bpf/xkernel

    Returns:
        0 on success, non-zero on failure
    """
    pin_dir = "/sys/fs/bpf/xkernel"

    if pin:
        subprocess.run(['sudo', 'mkdir', '-p', pin_dir], check=False)

    for bpf_file in bpf_files:
        if not os.path.exists(bpf_file):
            print(f"BPF file not found: {bpf_file}", file=sys.stderr)
            return 1

        print(f"Loading {bpf_file}...", file=sys.stderr)
        cmd = ['sudo', 'bpftool', 'prog', 'loadall', bpf_file, pin_dir, 'autoattach']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to load {bpf_file}: {result.stderr}", file=sys.stderr)
            return result.returncode
        print(f"Loaded and attached: {bpf_file}", file=sys.stderr)

    return 0


def load_critical_spans(cs_path):
    """Load critical spans into BPF maps using bpftool.

    Args:
        cs_path: Path to CS file

    Returns:
        0 on success, non-zero on failure
    """
    if not os.path.exists(cs_path):
        print(f"CS file not found: {cs_path}", file=sys.stderr)
        return 0  # Not an error - CS may not be needed

    with open(cs_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("CS file is empty, skipping critical span loading", file=sys.stderr)
        return 0

    # Parse and sort critical spans
    # Format: function_name,function_address,soff,eoff
    spans = []
    for line in lines:
        parts = line.split(',')
        if len(parts) < 4:
            continue
        func_addr = int(parts[1], 16)
        soff = int(parts[2], 16)
        eoff = int(parts[3], 16)
        spans.append((func_addr + soff, func_addr + eoff))

    # Sort by soff ascending, then by eoff descending
    spans.sort(key=lambda x: (x[0], -x[1]))

    # Update cs_len map
    cs_len = len(spans)
    key_hex = '00 00 00 00'
    # cs_len is __u32
    val_bytes = struct.pack('<I', cs_len)
    val_hex = ' '.join(f'{b:02x}' for b in val_bytes)

    result = subprocess.run(
        ['sudo', 'bpftool', 'map', 'update', 'name', '.bss.cs_len',
         'key', 'hex'] + key_hex.split() +
        ['value', 'hex'] + val_hex.split(),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: Failed to update cs_len: {result.stderr}", file=sys.stderr)

    # Update cs_map entries
    for i, (soff, eoff) in enumerate(spans):
        key_bytes = struct.pack('<I', i)
        key_hex = ' '.join(f'{b:02x}' for b in key_bytes)
        # critical_span struct: { u64 soff; u64 eoff; }
        val_bytes = struct.pack('<QQ', soff, eoff)
        val_hex = ' '.join(f'{b:02x}' for b in val_bytes)

        result = subprocess.run(
            ['sudo', 'bpftool', 'map', 'update', 'name', 'cs_map',
             'key', 'hex'] + key_hex.split() +
            ['value', 'hex'] + val_hex.split(),
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Warning: Failed to update cs_map[{i}]: {result.stderr}",
                  file=sys.stderr)

    print(f"Loaded {cs_len} critical spans", file=sys.stderr)
    return 0


def compile_single_bpf(bpf_c_path, bpf_dir):
    """Compile a single BPF .c file to .o.

    Args:
        bpf_c_path: Path to the .bpf.c source file
        bpf_dir: Path to the bpf/ directory (for include paths)

    Returns:
        Path to the compiled .bpf.o file, or None on failure
    """
    obj = bpf_c_path[:-2] + '.o'  # .bpf.c -> .bpf.o
    cmd = [
        'clang', '-g', '-O2', '-target', 'bpf',
        '-D__TARGET_ARCH_x86',
        f'-I{bpf_dir}',
        '-I/usr/include/bpf',
        '-c', bpf_c_path, '-o', obj,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to compile {bpf_c_path}: {result.stderr}", file=sys.stderr)
        return None
    return obj


def check_kprobe_optimized(func_name, offset):
    """Check if a kprobe at func+offset is jump-optimized.

    Reads /sys/kernel/debug/kprobes/list for the [OPTIMIZED] flag.

    Args:
        func_name: Kernel function name
        offset: Hex offset (int)

    Returns:
        True if the kprobe is jump-optimized
    """
    # Give the kernel a moment to optimize the kprobe
    time.sleep(0.5)
    result = subprocess.run(
        ['sudo', 'cat', '/sys/kernel/debug/kprobes/list'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False

    for line in result.stdout.splitlines():
        if func_name in line and f'+0x{offset:x}' in line:
            return '[OPTIMIZED]' in line
    return False


def patch_bpf_sec_offset(bpf_c_path, func_name, old_offset, new_offset):
    """Replace a SEC annotation offset in a BPF .c file.

    Patches both the SEC("kprobe/func+0xOLD") and the BPF_KPROBE(func_0xOLD)
    function name.

    Args:
        bpf_c_path: Path to the .bpf.c file
        func_name: Kernel function name
        old_offset: Current offset (int)
        new_offset: New offset (int)
    """
    with open(bpf_c_path, 'r') as f:
        content = f.read()

    safe_func = func_name.replace('.', '_').replace('-', '_')
    old_sec = f'SEC("kprobe/{func_name}+0x{old_offset:x}")'
    new_sec = f'SEC("kprobe/{func_name}+0x{new_offset:x}")'
    old_probe = f'BPF_KPROBE({safe_func}_0x{old_offset:x})'
    new_probe = f'BPF_KPROBE({safe_func}_0x{new_offset:x})'

    content = content.replace(old_sec, new_sec)
    content = content.replace(old_probe, new_probe)

    with open(bpf_c_path, 'w') as f:
        f.write(content)


def try_jump_optimization(bpf_c_path, bpf_dir):
    """Try candidate offsets for each kprobe to find jump-optimized ones.

    For each kprobe in the BPF file that has multiple candidates:
    1. Try each candidate offset
    2. Compile, load, check for [OPTIMIZED] flag
    3. Keep the first optimized offset, or fall back to the original

    Args:
        bpf_c_path: Path to the .bpf.c source file
        bpf_dir: Path to the bpf/ directory

    Returns:
        True if any kprobe was optimized, False otherwise
    """
    if not os.path.exists(bpf_c_path):
        print(f"BPF source not found: {bpf_c_path}", file=sys.stderr)
        return False

    with open(bpf_c_path, 'r') as f:
        lines = f.readlines()

    # Parse kprobe entries: find SEC annotations and their Candidates comments
    kprobes = []
    for i, line in enumerate(lines):
        m = re.match(r'// Candidates:\s*(.+)', line.strip())
        if m:
            candidates_str = m.group(1).strip()
            candidates = [int(c.strip(), 16) for c in candidates_str.split(',')]
            # Find the SEC line that follows (within next few lines)
            for j in range(i + 1, min(i + 5, len(lines))):
                sec_m = re.match(
                    r'SEC\("kprobe/([^"]+)\+0x([0-9a-fA-F]+)"\)',
                    lines[j].strip()
                )
                if sec_m:
                    func_name = sec_m.group(1)
                    current_offset = int(sec_m.group(2), 16)
                    kprobes.append({
                        'func_name': func_name,
                        'current_offset': current_offset,
                        'candidates': candidates,
                    })
                    break

    if not kprobes:
        print("No kprobe candidates found in BPF file", file=sys.stderr)
        return False

    pin_dir = "/sys/fs/bpf/xkernel_jumpopt_test"
    any_optimized = False

    # Back up the original source
    backup_path = bpf_c_path + '.jumpopt_backup'
    with open(bpf_c_path, 'r') as f:
        original_content = f.read()
    with open(backup_path, 'w') as f:
        f.write(original_content)

    # Track selected offsets per kprobe
    selected = {}

    for kp in kprobes:
        func_name = kp['func_name']
        original_offset = kp['current_offset']
        candidates = kp['candidates']

        if len(candidates) <= 1:
            print(f"  {func_name}+0x{original_offset:x}: single candidate, skipping",
                  file=sys.stderr)
            selected[func_name] = original_offset
            continue

        print(f"  {func_name}: trying {len(candidates)} candidates: "
              f"{', '.join(f'0x{c:x}' for c in candidates)}", file=sys.stderr)

        best_offset = original_offset
        current_file_offset = original_offset

        for cand in candidates:
            # Patch to this candidate
            if cand != current_file_offset:
                patch_bpf_sec_offset(bpf_c_path, func_name, current_file_offset, cand)
                current_file_offset = cand

            # Compile
            obj = compile_single_bpf(bpf_c_path, bpf_dir)
            if obj is None:
                print(f"    0x{cand:x}: compile failed, skipping", file=sys.stderr)
                continue

            # Load
            subprocess.run(['sudo', 'mkdir', '-p', pin_dir], check=False,
                           capture_output=True)
            result = subprocess.run(
                ['sudo', 'bpftool', 'prog', 'loadall', obj, pin_dir, 'autoattach'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"    0x{cand:x}: load failed, skipping", file=sys.stderr)
                subprocess.run(['sudo', 'rm', '-rf', pin_dir],
                               capture_output=True)
                continue

            # Check optimization
            optimized = check_kprobe_optimized(func_name, cand)

            # Unload test probe
            subprocess.run(['sudo', 'rm', '-rf', pin_dir], capture_output=True)
            time.sleep(0.3)

            if optimized:
                print(f"    0x{cand:x}: OPTIMIZED (selected)", file=sys.stderr)
                best_offset = cand
                any_optimized = True
                break
            else:
                print(f"    0x{cand:x}: not optimized", file=sys.stderr)

        selected[func_name] = best_offset

        # If we ended on a different offset than best, patch to best
        if current_file_offset != best_offset:
            patch_bpf_sec_offset(bpf_c_path, func_name, current_file_offset, best_offset)

    # Final compile with selected offsets
    print("  Final compile with selected offsets...", file=sys.stderr)
    obj = compile_single_bpf(bpf_c_path, bpf_dir)
    if obj is None:
        # Restore backup on failure
        print("  Final compile failed, restoring original", file=sys.stderr)
        with open(backup_path, 'r') as f:
            restored = f.read()
        with open(bpf_c_path, 'w') as f:
            f.write(restored)
        compile_single_bpf(bpf_c_path, bpf_dir)

    # Clean up backup
    if os.path.exists(backup_path):
        os.remove(backup_path)

    # Clean up test pin dir
    subprocess.run(['sudo', 'rm', '-rf', pin_dir], capture_output=True)

    return any_optimized


def get_runtime_state():
    """Read runtime state from disk.

    Returns:
        dict with keys 'kfuncs_loaded' (bool) and 'active_const_ids' (dict).
    """
    if not os.path.exists(RUNTIME_STATE_PATH):
        return {"kfuncs_loaded": False, "active_const_ids": {}}
    try:
        with open(RUNTIME_STATE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"kfuncs_loaded": False, "active_const_ids": {}}


def save_runtime_state(state):
    """Write runtime state to disk.

    Args:
        state: dict with 'kfuncs_loaded' and 'active_const_ids' keys.
    """
    os.makedirs(os.path.dirname(RUNTIME_STATE_PATH), exist_ok=True)
    with open(RUNTIME_STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)


def is_kfuncs_loaded():
    """Check if xk-kfuncs module is currently loaded.

    Returns:
        True if the module is loaded.
    """
    result = subprocess.run(
        ['lsmod'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        if line.startswith('xk_kfuncs '):
            return True
    return False


def ensure_kfuncs_loaded(project_root):
    """Idempotently load xk-kfuncs.ko.

    Args:
        project_root: Path to project root directory.

    Returns:
        True on success, False on failure.
    """
    if is_kfuncs_loaded():
        print("kfuncs module already loaded, skipping insmod", file=sys.stderr)
        return True

    kfuncs_path = os.path.join(project_root, 'kernel', 'kfuncs', 'xk-kfuncs.ko')
    if not os.path.exists(kfuncs_path):
        print(f"Error: kfuncs module not found: {kfuncs_path}", file=sys.stderr)
        return False

    print("Loading kfuncs module...", file=sys.stderr)
    result = subprocess.run(['sudo', 'insmod', kfuncs_path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to load kfuncs module: {result.stderr}", file=sys.stderr)
        return False

    state = get_runtime_state()
    state["kfuncs_loaded"] = True
    save_runtime_state(state)
    print("kfuncs module loaded", file=sys.stderr)
    return True


def snapshot_map_ids():
    """Snapshot all currently loaded BPF map IDs.

    Returns:
        set of integer map IDs
    """
    result = subprocess.run(
        ['sudo', 'bpftool', '-j', 'map', 'list'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return set()
    try:
        maps = json.loads(result.stdout)
        if not isinstance(maps, list):
            maps = [maps] if maps else []
        return {m['id'] for m in maps if 'id' in m}
    except (json.JSONDecodeError, TypeError, KeyError):
        return set()


def resolve_map_names(map_ids):
    """Resolve map names for a set of map IDs.

    Args:
        map_ids: set of integer map IDs

    Returns:
        dict mapping map name (str) to map ID (int)
    """
    if not map_ids:
        return {}

    result = subprocess.run(
        ['sudo', 'bpftool', '-j', 'map', 'list'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {}

    try:
        all_maps = json.loads(result.stdout)
        if not isinstance(all_maps, list):
            all_maps = [all_maps] if all_maps else []
    except (json.JSONDecodeError, TypeError):
        return {}

    name_to_id = {}
    for m in all_maps:
        mid = m.get('id')
        name = m.get('name', '')
        if mid in map_ids and name:
            name_to_id[name] = mid

    return name_to_id


def update_map_by_id(map_id, key_hex_str, val_hex_str):
    """Update a BPF map entry by map ID.

    Args:
        map_id: Integer map ID
        key_hex_str: Space-separated hex key (e.g. '00 00 00 00')
        val_hex_str: Space-separated hex value

    Returns:
        True on success, False on failure
    """
    result = subprocess.run(
        ['sudo', 'bpftool', 'map', 'update', 'id', str(map_id),
         'key', 'hex'] + key_hex_str.split() +
        ['value', 'hex'] + val_hex_str.split(),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: Failed to update map id {map_id}: {result.stderr}",
              file=sys.stderr)
        return False
    return True


def set_bss_variable(map_info, map_name, value):
    """Update a BSS variable using the map ID from map_info.

    BSS sections containing a single int/u32 have value_size=4.
    Packs the value as little-endian u32.

    Args:
        map_info: dict mapping map name to map ID (from load_and_attach_per_constid)
        map_name: BSS section name (e.g. '.bss.xk_mode')
        value: Integer value to set
    """
    map_id = map_info.get(map_name)
    if map_id is None:
        print(f"Warning: Map '{map_name}' not found in map_info "
              f"(available: {list(map_info.keys())})", file=sys.stderr)
        return False

    key_hex = '00 00 00 00'
    val_bytes = struct.pack('<I', value)
    val_hex = ' '.join(f'{b:02x}' for b in val_bytes)

    return update_map_by_id(map_id, key_hex, val_hex)


def load_and_attach_per_constid(bpf_files, const_id, mode):
    """Load and attach BPF programs for a specific ConstID.

    Creates per-ConstID pin directories, loads programs with pinmaps,
    collects map info via program introspection, and sets xk_mode.
    For mode 0 (Immediate), also sets xk_active=1.

    Args:
        bpf_files: List of .bpf.o file paths
        const_id: ConstID string
        mode: Consistency mode (0=Immediate, 1=Per-task, 2=Global)

    Returns:
        (return_code, map_info) tuple. return_code 0 on success.
        map_info is a dict mapping map name to map ID.
    """
    progs_dir = f"{BPF_PIN_BASE}/{const_id}/progs"
    maps_dir = f"{BPF_PIN_BASE}/{const_id}/maps"

    subprocess.run(['sudo', 'mkdir', '-p', progs_dir], check=False,
                   capture_output=True)
    subprocess.run(['sudo', 'mkdir', '-p', maps_dir], check=False,
                   capture_output=True)

    # Snapshot map IDs before loading so we can find newly created maps
    maps_before = snapshot_map_ids()

    for bpf_file in bpf_files:
        if not os.path.exists(bpf_file):
            print(f"BPF file not found: {bpf_file}", file=sys.stderr)
            return 1, {}

        print(f"Loading {bpf_file} for ConstID {const_id}...", file=sys.stderr)
        cmd = ['sudo', 'bpftool', 'prog', 'loadall', bpf_file,
               progs_dir, 'autoattach', 'pinmaps', maps_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to load {bpf_file}: {result.stderr}", file=sys.stderr)
            return result.returncode, {}
        print(f"Loaded and attached: {bpf_file}", file=sys.stderr)

    # Find newly created maps by diffing before/after
    maps_after = snapshot_map_ids()
    new_map_ids = maps_after - maps_before
    map_info = resolve_map_names(new_map_ids)
    print(f"Discovered maps: {list(map_info.keys())}", file=sys.stderr)

    # Set consistency mode
    set_bss_variable(map_info, '.bss.xk_mode', mode)

    # Mode 0 (Immediate): activate right away
    if mode == 0:
        set_bss_variable(map_info, '.bss.xk_active', 1)

    return 0, map_info


def activate_constid(const_id, map_info):
    """Activate a ConstID by setting xk_active=1.

    Args:
        const_id: ConstID string
        map_info: dict mapping map name to map ID
    """
    return set_bss_variable(map_info, '.bss.xk_active', 1)


def unload_constid(const_id):
    """Unload BPF programs for a specific ConstID.

    Removes the per-ConstID pin directory, which detaches all BPF programs.

    Args:
        const_id: ConstID string
    """
    pin_dir = f"{BPF_PIN_BASE}/{const_id}"
    print(f"Unloading ConstID {const_id}...", file=sys.stderr)
    result = subprocess.run(['sudo', 'rm', '-rf', pin_dir],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Failed to remove {pin_dir}: {result.stderr}",
              file=sys.stderr)
        return False

    # Update runtime state
    state = get_runtime_state()
    state["active_const_ids"].pop(str(const_id), None)
    save_runtime_state(state)
    return True


def load_critical_spans_for_constid(cs_path, const_id, map_info):
    """Load critical spans into BPF maps for a specific ConstID.

    Uses map IDs (from before/after diff at load time) to target the
    correct per-ConstID maps, avoiding issues with BSS maps not being
    auto-pinned by bpftool.

    Args:
        cs_path: Path to CS file
        const_id: ConstID string
        map_info: dict mapping map name to map ID.

    Returns:
        0 on success, non-zero on failure
    """
    if not os.path.exists(cs_path):
        print(f"CS file not found: {cs_path}", file=sys.stderr)
        return 0

    with open(cs_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("CS file is empty, skipping critical span loading", file=sys.stderr)
        return 0

    spans = []
    for line in lines:
        parts = line.split(',')
        if len(parts) < 4:
            continue
        func_addr = int(parts[1], 16)
        soff = int(parts[2], 16)
        eoff = int(parts[3], 16)
        spans.append((func_addr + soff, func_addr + eoff))

    spans.sort(key=lambda x: (x[0], -x[1]))

    # Update cs_len via map ID
    cs_len = len(spans)
    cs_len_id = map_info.get('.bss.cs_len')
    if cs_len_id is not None:
        key_hex = '00 00 00 00'
        val_bytes = struct.pack('<I', cs_len)
        val_hex = ' '.join(f'{b:02x}' for b in val_bytes)
        update_map_by_id(cs_len_id, key_hex, val_hex)
    else:
        print("Warning: .bss.cs_len map not found, skipping cs_len update",
              file=sys.stderr)

    # Update cs_map entries via map ID
    cs_map_id = map_info.get('cs_map')
    if cs_map_id is not None:
        for i, (soff, eoff) in enumerate(spans):
            key_bytes = struct.pack('<I', i)
            key_hex = ' '.join(f'{b:02x}' for b in key_bytes)
            val_bytes = struct.pack('<QQ', soff, eoff)
            val_hex = ' '.join(f'{b:02x}' for b in val_bytes)
            update_map_by_id(cs_map_id, key_hex, val_hex)
    else:
        print("Warning: cs_map not found, skipping cs_map update",
              file=sys.stderr)

    print(f"Loaded {cs_len} critical spans for ConstID {const_id}", file=sys.stderr)
    return 0


def load_safe_spans_for_constid(ss_path, const_id, map_info):
    """Load safe spans into BPF ss_map for a specific ConstID.

    Uses map IDs to target the correct per-ConstID maps.
    Falls back silently if ss_map is not present (backward compatible).

    Args:
        ss_path: Path to SS file (same format as CS file)
        const_id: ConstID string
        map_info: dict mapping map name to map ID.

    Returns:
        0 on success, non-zero on failure
    """
    if not os.path.exists(ss_path):
        print(f"SS file not found: {ss_path}, skipping SS loading", file=sys.stderr)
        return 0

    with open(ss_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("SS file is empty, skipping safe span loading", file=sys.stderr)
        return 0

    # Parse spans (same format as CS: function_name,function_address,soff,eoff)
    spans = []
    for line in lines:
        parts = line.split(',')
        if len(parts) < 4:
            continue
        func_addr = int(parts[1], 16)
        soff = int(parts[2], 16)
        eoff = int(parts[3], 16)
        spans.append((func_addr + soff, func_addr + eoff))

    spans.sort(key=lambda x: (x[0], -x[1]))

    # Update ss_len via map ID
    span_count = len(spans)
    ss_len_id = map_info.get('.bss.ss_len')
    if ss_len_id is not None:
        key_hex = '00 00 00 00'
        val_bytes = struct.pack('<I', span_count)
        val_hex = ' '.join(f'{b:02x}' for b in val_bytes)
        update_map_by_id(ss_len_id, key_hex, val_hex)
    else:
        print("Warning: .bss.ss_len map not found, skipping ss_len update",
              file=sys.stderr)
        return 0

    # Update ss_map entries via map ID
    ss_map_id = map_info.get('ss_map')
    if ss_map_id is not None:
        for i, (soff, eoff) in enumerate(spans):
            key_bytes = struct.pack('<I', i)
            key_hex = ' '.join(f'{b:02x}' for b in key_bytes)
            val_bytes = struct.pack('<QQ', soff, eoff)
            val_hex = ' '.join(f'{b:02x}' for b in val_bytes)
            update_map_by_id(ss_map_id, key_hex, val_hex)
    else:
        print("Warning: ss_map not found, skipping ss_map update",
              file=sys.stderr)

    print(f"Loaded {span_count} safe spans for ConstID {const_id}", file=sys.stderr)
    return 0


def main():
    """Main entry point for standalone loader usage."""
    import argparse
    parser = argparse.ArgumentParser(description='Xkernel BPF Loader')
    parser.add_argument('--files', required=True,
                        help='Comma-separated BPF .o files to load')
    parser.add_argument('--pin', action='store_true',
                        help='Pin BPF programs to filesystem')
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bpf_dir = os.path.join(project_root, 'bpf')

    # Generate cs_artifact header
    cs_artifact_path = os.path.join(bpf_dir, 'cs_artifact.bpf.h')
    generate_cs_artifact_header(CS_PATH, cs_artifact_path)

    # Recompile BPF programs
    compile_bpf_programs(bpf_dir)

    # Load and attach
    files = [f.strip() for f in args.files.split(',') if f.strip()]
    ret = load_and_attach(files, pin=args.pin)
    if ret != 0:
        sys.exit(ret)

    # Load critical spans if available
    load_critical_spans(CS_PATH)


if __name__ == "__main__":
    main()
