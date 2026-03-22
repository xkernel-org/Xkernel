#!/usr/bin/env python3
"""Xkernel command-line interface.

Replaces the bash xkernel-tool script. Provides build, load, unload,
table, and trace commands.
"""

import os
import re
import subprocess
import sys
import time


SCOPE_TABLE = "/dev/shm/xkernel/scope_table"
CS_RAW = "/dev/shm/xkernel/cs_raw"
CS_FILE = "/dev/shm/xkernel/cs"
SS_RAW = "/dev/shm/xkernel/ss_raw"
SS_FILE = "/dev/shm/xkernel/ss"


def get_project_root():
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def update_status(const_id, new_status):
    """Update status for a ConstID in the scope table."""
    if not os.path.exists(SCOPE_TABLE):
        return
    with open(SCOPE_TABLE, 'r') as f:
        lines = f.readlines()
    if not lines:
        return

    header = lines[0].rstrip('\n').split('\t')
    try:
        cid_col = header.index('ConstID')
        st_col = header.index('Status')
    except ValueError:
        return

    out = [lines[0]]
    for line in lines[1:]:
        fields = line.rstrip('\n').split('\t')
        if len(fields) > max(cid_col, st_col) and fields[cid_col] == str(const_id):
            fields[st_col] = new_status
        out.append('\t'.join(fields) + '\n')

    with open(SCOPE_TABLE, 'w') as f:
        f.writelines(out)


def update_status_by_file(bpf_file, new_status):
    """Update status for all entries matching a BPF file."""
    if not os.path.exists(SCOPE_TABLE):
        return
    with open(SCOPE_TABLE, 'r') as f:
        lines = f.readlines()
    if not lines:
        return

    header = lines[0].rstrip('\n').split('\t')
    try:
        bf_col = header.index('BPF_File')
        st_col = header.index('Status')
    except ValueError:
        return

    out = [lines[0]]
    for line in lines[1:]:
        fields = line.rstrip('\n').split('\t')
        if len(fields) > max(bf_col, st_col) and fields[bf_col] == bpf_file:
            fields[st_col] = new_status
        out.append('\t'.join(fields) + '\n')

    with open(SCOPE_TABLE, 'w') as f:
        f.writelines(out)


def update_all_status(new_status):
    """Update status for all entries in the scope table."""
    if not os.path.exists(SCOPE_TABLE):
        return
    with open(SCOPE_TABLE, 'r') as f:
        lines = f.readlines()
    if not lines:
        return

    header = lines[0].rstrip('\n').split('\t')
    try:
        st_col = header.index('Status')
    except ValueError:
        return

    out = [lines[0]]
    for line in lines[1:]:
        fields = line.rstrip('\n').split('\t')
        if len(fields) > st_col:
            fields[st_col] = new_status
        out.append('\t'.join(fields) + '\n')

    with open(SCOPE_TABLE, 'w') as f:
        f.writelines(out)


def resolve_func_addr(func_name):
    """Resolve function address from /proc/kallsyms."""
    try:
        result = subprocess.run(
            ['sudo', 'grep', '-E', f'^[0-9a-f]+ [tT] {func_name}$',
             '/proc/kallsyms'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            addr = result.stdout.strip().split()[0]
            return f"0x{addr}"
    except Exception:
        pass
    return None


def generate_cs_file(const_ids_str):
    """Generate CS file from cs_raw for specified ConstIDs.

    Args:
        const_ids_str: Comma-separated ConstIDs
    """
    if not os.path.exists(CS_RAW):
        print(f"Warning: CS_RAW file not found at {CS_RAW}")
        return False

    const_ids = set(const_ids_str.split(','))

    # Clear existing CS file
    with open(CS_FILE, 'w') as f:
        pass

    # Read cs_raw (skip header) and generate cs entries
    # Format: ConstID\tFunctionName\tStartOffset\tEndOffset
    entries = []
    with open(CS_RAW, 'r') as f:
        header = f.readline()  # skip header
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            cid, func_name, soff, eoff = parts[0], parts[1], parts[2], parts[3]
            if cid in const_ids:
                func_addr = resolve_func_addr(func_name)
                if func_addr:
                    entries.append(f"{func_name},{func_addr},{soff},{eoff}")
                else:
                    print(f"Warning: Could not resolve address for function {func_name}")

    if entries:
        with open(CS_FILE, 'w') as f:
            f.write('\n'.join(entries) + '\n')
        print(f"Generated CS file: {CS_FILE}")
        return True
    else:
        print("Warning: No CS entries generated")
        return False


def generate_ss_file(const_ids_str):
    """Generate SS file for specified ConstIDs.

    Priority: ss_raw (populated during build) > CS file fallback.

    Args:
        const_ids_str: Comma-separated ConstIDs
    """
    const_ids = set(const_ids_str.split(','))

    # Clear existing SS file
    with open(SS_FILE, 'w') as f:
        pass

    entries = []
    has_ss_raw = False  # True if ss_raw has any rows for the requested ConstIDs

    # Priority 1: Read from ss_raw (populated during build from safe_spans or CS fallback)
    if os.path.exists(SS_RAW):
        with open(SS_RAW, 'r') as f:
            header = f.readline()  # skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue
                cid, func_name, soff, eoff = parts[0], parts[1], parts[2], parts[3]
                if cid in const_ids:
                    has_ss_raw = True
                    if soff == eoff:
                        print(f"SS: skipping {func_name} (soff == eoff, zero-width span)")
                        continue
                    func_addr = resolve_func_addr(func_name)
                    if func_addr:
                        entries.append(f"{func_name},{func_addr},{soff},{eoff}")
                    else:
                        print(f"Warning: Could not resolve address for function {func_name} (SS)")

    # Priority 2: Fall back to CS file only if ss_raw had NO data for these ConstIDs
    if not has_ss_raw and not entries and os.path.exists(CS_FILE):
        with open(CS_FILE, 'r') as f:
            entries = [l.strip() for l in f if l.strip()]
        if entries:
            print("SS: falling back to CS entries (no ss_raw data)")

    if entries:
        with open(SS_FILE, 'w') as f:
            f.write('\n'.join(entries) + '\n')
        print(f"Generated SS file: {SS_FILE}")
        return True
    else:
        print("Warning: No SS entries generated")
        return False


def cmd_build(args):
    """Build pipeline: gen -> codegen -> compile.

    Usage:
      xkernel-tool build <config.toml>           # Build single tunable from TOML config
      xkernel-tool build --all                    # Rebuild all from testcases.py (legacy)
    """
    project_root = get_project_root()
    skip_gen = '--skip-gen' in args
    verbose = '--verbose' in args or '-v' in args
    run_analysis = '--run-analysis' in args

    # Separate flags from positional args
    flags = {'--skip-gen', '--verbose', '-v', '--all', '--run-analysis'}
    positional = [a for a in args if a not in flags]
    use_all = '--all' in args

    # Detect mode: TOML file or legacy --all
    toml_file = None
    if positional:
        candidate = positional[0]
        if candidate.endswith('.toml') or os.path.isfile(candidate):
            toml_file = candidate

    if toml_file:
        _cmd_build_single(toml_file, skip_gen, verbose, run_analysis, project_root)
    elif use_all:
        _cmd_build_all(skip_gen, verbose, run_analysis, project_root)
    else:
        print("Usage: xkernel-tool build <config.toml> [--skip-gen] [--run-analysis] [--verbose/-v]")
        print("       xkernel-tool build --all [--skip-gen] [--run-analysis] [--verbose/-v]")
        print()
        print("  <config.toml>  Build a single tunable from a TOML config file")
        print("  --all          Rebuild all tunables from tunables/all.toml (clean rebuild)")
        sys.exit(1)


def _cmd_build_single(toml_file, skip_gen, verbose, run_analysis, project_root):
    """Build tunables from a TOML config file (single or multi-tunable)."""
    from src.config import load_configs
    from src.codegen import next_const_id, run_codegen_single

    if not os.path.exists(toml_file):
        print(f"Error: Config file not found: {toml_file}")
        sys.exit(1)

    kernel_dir, configs = load_configs(toml_file, run_analysis=run_analysis)
    if not configs:
        print(f"Error: No tunables found in {toml_file}")
        sys.exit(1)

    print("==========================================")
    print(f"Xkernel Build: {len(configs)} tunable(s) from {toml_file}")
    print(f"  Kernel source: {kernel_dir}")
    print("==========================================")

    assigned_ids = []

    for i, config in enumerate(configs):
        const_id = next_const_id()
        assigned_ids.append((config.name, const_id))

        print(f"\n--- [{i+1}/{len(configs)}] {config.name} (ConstID={const_id}) ---")

        # Step 1: Generate BB files
        if not skip_gen:
            print(f"  [Step 1/3] Running gen.py for {config.name}...")
            from src.gen import generate_bb_files_single
            result = generate_bb_files_single(config, const_id, kernel_dir=kernel_dir)
            if result is None:
                print(f"  Error: BB file generation failed for {config.name}, skipping")
                continue
        else:
            print("  [Step 1/3] Skipped gen.py (--skip-gen)")

        # Step 2: Run codegen
        print(f"  [Step 2/3] Running codegen for ConstID {const_id}...")
        run_codegen_single(config, const_id, verbose=verbose)

    # Step 3: Compile all BPF programs at once
    print("\n[Step 3/3] Compiling BPF programs...")
    print("==========================================")
    bpf_dir = os.path.join(project_root, 'bpf')
    ret = subprocess.run(['make', f'-j{os.cpu_count()}'], cwd=bpf_dir)
    if ret.returncode != 0:
        print("Error: BPF compilation failed")
        sys.exit(1)

    BOLD = '\033[1m'
    GREEN = '\033[32m'
    CYAN = '\033[36m'
    DIM = '\033[2m'
    RST = '\033[0m'

    print(f"\n{BOLD}=========================================={RST}")
    print(f"{BOLD}Build completed: {len(assigned_ids)} tunable(s){RST}")
    for name, cid in assigned_ids:
        print(f"  {GREEN}{name}{RST} -> ConstID {BOLD}{cid}{RST}")
    print(f"{BOLD}=========================================={RST}")
    print(f"\n{BOLD}Next steps:{RST}")
    print(f"  {CYAN}1. Edit your X-tune policy:{RST}")
    for name, cid in assigned_ids:
        stub_path = os.path.join('bpf', 'stubs', f'xtune_stub_{cid}.bpf.c')
        print(f"     {GREEN}{stub_path}{RST}  {DIM}# {name}{RST}")
    print(f"  {CYAN}2. Load:{RST}")
    for name, cid in assigned_ids:
        print(f"     {GREEN}sudo ./xkernel-tool load <MODE> {cid}{RST}  {DIM}# {name}{RST}")


def _cmd_build_all(skip_gen, verbose, run_analysis, project_root):
    """Batch build: rebuild all tunables from tunables/all.toml."""
    from src.codegen import clear_all_tables
    clear_all_tables()
    print("Cleared all tables for full rebuild")

    all_toml = os.path.join(project_root, 'tunables', 'all.toml')
    if not os.path.exists(all_toml):
        print(f"Error: {all_toml} not found")
        sys.exit(1)

    _cmd_build_single(all_toml, skip_gen, verbose, run_analysis, project_root)


def resolve_constid_to_bpf(const_id, project_root):
    """Resolve a ConstID to its BPF .o file path via the scope table.

    Args:
        const_id: ConstID string
        project_root: Project root directory

    Returns:
        (bpf_o_path, bpf_filename) tuple, or (None, None) if not found.
    """
    if not os.path.exists(SCOPE_TABLE):
        print(f"Error: Scope Table not found at {SCOPE_TABLE}")
        return None, None

    bpf_file = None
    with open(SCOPE_TABLE, 'r') as f:
        lines = f.readlines()
    if lines:
        header = lines[0].rstrip('\n').split('\t')
        try:
            cid_col = header.index('ConstID')
            bf_col = header.index('BPF_File')
        except ValueError:
            pass
        else:
            for line in lines[1:]:
                fields = line.rstrip('\n').split('\t')
                if len(fields) > max(cid_col, bf_col) and fields[cid_col] == const_id:
                    bpf_file = fields[bf_col]
                    break

    if not bpf_file:
        return None, None

    full_path = os.path.join(project_root, 'bpf', 'stubs', bpf_file)
    return full_path, bpf_file


def _parse_kprobes_from_bpf_c(bpf_c_path):
    """Parse X_TUNE kprobe entries from a generated BPF .c file's comments.

    Returns list of dicts with keys: num, location, type, rel, role.
    """
    if not os.path.exists(bpf_c_path):
        return []

    with open(bpf_c_path, 'r') as f:
        lines = f.readlines()

    kprobes = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'// Kprobe (\d+)[ab]?:\s+(.+?\+0x[0-9a-fA-F]+)(?:\s+\((.+?)\))?\s*$', line)
        if m:
            kp_num = m.group(1)
            location = m.group(2)
            kp_type = m.group(3) or 'simple'

            if 'SAVE' in kp_type:
                i += 1
                continue
            if 'APPLY' in kp_type:
                kp_type = 'irreversible'

            # Look ahead for // Relationship: line
            rel = ''
            for j in range(i + 1, min(i + 4, len(lines))):
                rm = re.match(r'// Relationship:\s+(.+)', lines[j].strip())
                if rm:
                    rel = rm.group(1)
                    break

            kprobes.append({
                'num': kp_num,
                'location': location,
                'type': kp_type,
                'rel': rel,
                'role': 'tune',
            })
        i += 1
    return kprobes


def _parse_kprobes_from_internal_header(internal_h_path):
    """Parse SAVE kprobes from the internal .bpf.h header (irreversible synthesis).

    Returns list of dicts with keys: location, comment, role.
    """
    if not os.path.exists(internal_h_path):
        return []

    with open(internal_h_path, 'r') as f:
        lines = f.readlines()

    kprobes = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        # Match: // Save handler N: func+0xOFFSET (fires BEFORE mnemonic)
        m = re.match(r'// Save handler \d+:\s+(.+?\+0x[0-9a-fA-F]+)\s+\((.+?)\)', line)
        if m:
            kprobes.append({
                'location': m.group(1),
                'comment': m.group(2),
                'role': 'save',
            })
    return kprobes


def _parse_kprobes_from_cs_artifact(cs_artifact_path):
    """Parse guard/unguard kprobes from cs_artifact.bpf.h.

    Returns list of dicts with keys: location, role ('guard' or 'unguard').
    """
    if not os.path.exists(cs_artifact_path):
        return []

    with open(cs_artifact_path, 'r') as f:
        lines = f.readlines()

    kprobes = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        # Match comment lines: // Guard: func+0xOFF (SS entry) or // Unguard: func+0xOFF (SS exit)
        m = re.match(r'// (Guard|Unguard):\s+(.+?\+0x[0-9a-fA-F]+)\s+\(SS (entry|exit)\)', line)
        if m:
            kprobes.append({
                'location': m.group(2),
                'role': m.group(1).lower(),  # 'guard' or 'unguard'
            })
    return kprobes


def print_loaded_kprobes(const_id, bpf_c_path, mode):
    """Print a visual summary of all attached BPF kprobes after loading.

    Shows three categories:
    1. X_TUNE kprobes (from .bpf.c) — the actual constant-tuning probes
    2. SAVE kprobes (from stub .bpf.h) — irreversible synthesis pre-save
    3. Transition kprobes (from cs_artifact.bpf.h) — per-task/global transition handlers
    """
    mode_names = {0: 'Immediate', 1: 'Per-task', 2: 'Global'}
    mode_name = mode_names.get(mode, str(mode))

    # Collect kprobes from all sources
    tune_kprobes = _parse_kprobes_from_bpf_c(bpf_c_path)

    # Stub header: same dir, same prefix but .bpf.h
    internal_h = bpf_c_path.replace('.bpf.c', '.bpf.h')
    save_kprobes = _parse_kprobes_from_internal_header(internal_h)

    # cs_artifact.bpf.h: in bpf/ directory
    bpf_dir = os.path.dirname(os.path.dirname(bpf_c_path))  # bpf/stubs/ -> bpf/
    cs_artifact = os.path.join(bpf_dir, 'cs_artifact.bpf.h')
    transition_kprobes = _parse_kprobes_from_cs_artifact(cs_artifact)

    if not tune_kprobes and not save_kprobes and not transition_kprobes:
        return

    # ANSI helpers
    DIM = '\033[2m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    RST = '\033[0m'

    W = 62

    def box_line(content, pad_len):
        return f"  {DIM}\u2502{RST} {content}{' ' * max(0, pad_len)}{DIM}\u2502{RST}"

    print()
    print(f"  {DIM}\u250c{'─' * W}\u2510{RST}")
    title = f"Loaded Kprobes — ConstID {const_id} ({mode_name})"
    print(box_line(f"{BOLD}{title}{RST}", W - 1 - len(title)))
    print(f"  {DIM}\u251c{'─' * W}\u2524{RST}")

    # Section: X_TUNE kprobes
    items = []
    for kp in tune_kprobes:
        loc = f"kprobe/{kp['location']}"
        detail = f"Type: {kp['type']}"
        if kp['rel']:
            detail += f"    Expr: {kp['rel']}"
        items.append((f"{GREEN}\u25b6{RST} {loc}", detail))

    # Section: SAVE kprobes (irreversible)
    for kp in save_kprobes:
        loc = f"kprobe/{kp['location']}"
        items.append((f"{YELLOW}\u25c0{RST} {loc}", kp['comment']))

    # Section: guard/unguard kprobes (transition)
    for kp in transition_kprobes:
        loc = f"kprobe/{kp['location']}"
        role = kp.get('role', 'guard')
        if role == 'guard':
            items.append((f"{CYAN}\u25b7{RST} {loc}", "guard (SS entry)"))
        else:
            items.append((f"{CYAN}\u25c1{RST} {loc}", "unguard (SS exit)"))

    for i, (loc_line, detail_line) in enumerate(items):
        # loc_line contains ANSI codes, compute visible length
        vis_loc = re.sub(r'\033\[[0-9;]*m', '', loc_line)
        print(box_line(f" {loc_line}", W - 2 - len(vis_loc)))
        print(box_line(f"   {DIM}{detail_line}{RST}", W - 4 - len(detail_line)))
        if i < len(items) - 1:
            print(box_line("", W - 1))

    print(f"  {DIM}\u2514{'─' * W}\u2518{RST}")


def cmd_load(args):
    """Load BPF kprobes for a single ConstID with per-ConstID lifecycle."""
    from src.loader import (
        ensure_kfuncs_loaded, load_and_attach_per_constid,
        load_critical_spans_for_constid, load_safe_spans_for_constid,
        activate_constid,
        generate_cs_artifact_header, compile_single_bpf,
        get_runtime_state, save_runtime_state,
    )

    # Detect --jump-opt flag
    jump_opt = '--jump-opt' in args
    args = [a for a in args if a != '--jump-opt']

    if len(args) < 2:
        print("Usage: xkernel-tool load <mode> <constID> [timeout] [--jump-opt]")
        print("  mode: 0=Immediate, 1=Per-task, 2=Global")
        sys.exit(1)

    mode = int(args[0])
    if mode not in (0, 1, 2):
        print(f"Invalid mode: {mode}")
        sys.exit(1)

    const_id = args[1]
    if not re.match(r'^\d+$', const_id):
        print(f"Error: ConstID must be a number, got: {const_id}")
        sys.exit(1)

    project_root = get_project_root()

    # Check if this ConstID is already active
    state = get_runtime_state()
    if const_id in state.get("active_const_ids", {}):
        print(f"Error: ConstID {const_id} is already loaded. "
              f"Unload it first with: xkernel-tool unload {const_id}")
        sys.exit(1)

    # Resolve ConstID -> BPF file
    bpf_o_path, bpf_filename = resolve_constid_to_bpf(const_id, project_root)
    if not bpf_o_path:
        print(f"Error: ConstID {const_id} not found in Scope Table")
        sys.exit(1)
    if not os.path.exists(bpf_o_path.replace('.bpf.o', '.bpf.c')):
        print(f"Error: BPF source not found for ConstID {const_id}")
        sys.exit(1)

    # Step 1: Generate CS and SS files for this ConstID
    print(f"Generating CS file for ConstID: {const_id}")
    generate_cs_file(const_id)
    print(f"Generating SS file for ConstID: {const_id}")
    generate_ss_file(const_id)

    # Step 2: Generate cs_artifact (guard/unguard kprobes from SS ranges) and compile BPF
    # Guard/unguard kprobes are only needed for Per-task mode (mode 1).
    # Immediate mode needs no transition; Global mode uses kernel module kprobes.
    bpf_dir = os.path.join(project_root, 'bpf')
    cs_artifact_path = os.path.join(bpf_dir, 'cs_artifact.bpf.h')
    if mode == 1:
        spans_file = SS_FILE if os.path.exists(SS_FILE) else CS_FILE
        generate_cs_artifact_header(spans_file, cs_artifact_path)
    else:
        # Write empty cs_artifact — no guard/unguard kprobes needed
        with open(cs_artifact_path, 'w') as f:
            f.write("#ifndef __CS_ARTIFACT_BPF_H__\n"
                    "#define __CS_ARTIFACT_BPF_H__\n"
                    "#include \"xkernel.bpf.h\"\n"
                    "#endif\n")

    print("Compiling BPF files...")
    bpf_c = bpf_o_path.replace('.bpf.o', '.bpf.c')
    obj = compile_single_bpf(bpf_c, bpf_dir)
    if obj is None:
        print(f"Error: Failed to compile {os.path.basename(bpf_c)}")
        sys.exit(1)
    print(f"  Compiled: {os.path.basename(bpf_c)}")

    # Step 3: Ensure kfuncs module is loaded (idempotent)
    # Must be before jump-opt probing since BPF programs use kfuncs
    if not ensure_kfuncs_loaded(project_root):
        print("Failed to load kfuncs module")
        sys.exit(1)

    # Step 4: Jump optimization (optional)
    if jump_opt:
        from src.loader import try_jump_optimization
        print("\n--- Jump Optimization ---")
        print("Probing candidate offsets for jump-optimized kprobes...")
        optimized = try_jump_optimization(bpf_c, bpf_dir)
        if optimized:
            print(f"  Jump optimization applied to {os.path.basename(bpf_c)}")
        else:
            print(f"  No jump-optimizable offsets found in {os.path.basename(bpf_c)}")
        print("--- End Jump Optimization ---\n")

    # Step 5: Load and attach BPF programs (per-ConstID)
    mode_names = {0: 'Immediate', 1: 'Per-task', 2: 'Global'}
    print(f"Loading BPF for ConstID {const_id} (mode={mode_names[mode]}):")
    print(f"  File: {bpf_o_path}")
    ret, map_info = load_and_attach_per_constid([bpf_o_path], const_id, mode)
    if ret != 0:
        print(f"Failed to load kprobes for ConstID {const_id}.")
        sys.exit(ret)

    # Step 6: Load critical spans and safe spans into BPF maps
    load_critical_spans_for_constid(CS_FILE, const_id, map_info)
    load_safe_spans_for_constid(SS_FILE, const_id, map_info)

    # Step 7: Mode 2 (Global) — load consistency module, wait, activate
    if mode == 2:
        print("Loading global consistency module for transition...")
        consistency_path = os.path.join(project_root, 'kernel', 'consistency',
                                        'xk-consistency.ko')
        if not os.path.exists(consistency_path):
            print(f"Error: Consistency module not found: {consistency_path}")
            print("Cleaning up loaded BPF programs...")
            from src.loader import unload_constid
            unload_constid(const_id)
            sys.exit(1)

        timeout_val = int(args[2]) if len(args) > 2 else 5

        # Capture dmesg baseline before insmod
        dmesg_before = subprocess.run(
            ['sudo', 'dmesg'], capture_output=True, text=True
        )
        baseline_lines = len(dmesg_before.stdout.splitlines()) if dmesg_before.returncode == 0 else 0

        cmd = ['sudo', 'insmod', consistency_path, f'timeout_sec={timeout_val}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: Failed to load consistency module: {result.stderr}")
            # Show NEW kernel messages (after baseline) for debugging
            dmesg_after = subprocess.run(
                ['sudo', 'dmesg'], capture_output=True, text=True
            )
            if dmesg_after.returncode == 0 and dmesg_after.stdout:
                all_lines = dmesg_after.stdout.strip().splitlines()
                new_lines = all_lines[baseline_lines:]
                if new_lines:
                    print("Kernel messages from consistency module init:")
                    for line in new_lines:
                        print(f"  {line}")
                else:
                    # Fallback: show last 15 lines
                    recent = all_lines[-15:] if len(all_lines) > 15 else all_lines
                    print("Recent kernel messages (dmesg):")
                    for line in recent:
                        print(f"  {line}")
            # Clean up: unload the BPF programs we just loaded
            print(f"Cleaning up BPF programs for ConstID {const_id}...")
            from src.loader import unload_constid
            unload_constid(const_id)
            sys.exit(1)
        else:
            print("Consistency module loaded. Waiting for transition...")
            # Poll for new dmesg lines indicating transition status
            max_wait = timeout_val + 5
            transition_done = False
            for _ in range(max_wait * 10):  # Check every 100ms
                time.sleep(0.1)
                dmesg_poll = subprocess.run(
                    ['sudo', 'dmesg'], capture_output=True, text=True
                )
                if dmesg_poll.returncode != 0:
                    continue
                new_lines = dmesg_poll.stdout.splitlines()[baseline_lines:]
                for line in reversed(new_lines):
                    if 'transition done' in line or 'transition instant' in line:
                        transition_done = True
                        break
                    if 'transition timed out' in line:
                        print("Warning: Global transition failed (timeout)")
                        break
                if transition_done or any('transition timed out' in l for l in new_lines):
                    break
            if not transition_done:
                print(f"Warning: Transition status unclear after {max_wait}s")
            # Activate the ConstID
            activate_constid(const_id, map_info)
            print(f"ConstID {const_id} activated after global transition.")
            # Unload consistency module (mission accomplished)
            subprocess.run(['sudo', 'rmmod', 'xk-consistency'],
                           capture_output=True)
            print("Consistency module unloaded.")

    # Step 8: Update scope table + runtime state
    update_status(const_id, "active")
    state = get_runtime_state()
    if "active_const_ids" not in state:
        state["active_const_ids"] = {}
    state["active_const_ids"][const_id] = {
        "mode": mode,
        "bpf_file": bpf_filename,
        "status": "active"
    }
    save_runtime_state(state)

    # Show loaded kprobes summary
    print_loaded_kprobes(const_id, bpf_c, mode)

    print(f"\nConstID {const_id} loaded successfully (mode={mode_names[mode]}).")


def cmd_unload(args):
    """Unload BPF kprobes for specific ConstIDs or all."""
    from src.loader import (
        unload_constid, is_kfuncs_loaded,
        get_runtime_state, save_runtime_state,
    )

    # Unload consistency module if loaded (safety measure)
    subprocess.run(['sudo', 'rmmod', 'xk-consistency'],
                   capture_output=True)

    state = get_runtime_state()
    active = state.get("active_const_ids", {})

    if '--all' in args or not args:
        # Unload all active ConstIDs
        if not active:
            print("No active ConstIDs to unload.")
        else:
            for cid in list(active.keys()):
                unload_constid(cid)
                update_status(cid, "ready")
            print(f"Unloaded {len(active)} ConstID(s).")

        # Give BPF time to detach
        time.sleep(2)

        # Unload kfuncs module if loaded
        if is_kfuncs_loaded():
            print("Unloading kfuncs module...")
            result = subprocess.run(['sudo', 'rmmod', 'xk-kfuncs'],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Failed to unload kfuncs: {result.stderr}")
            else:
                print("kfuncs module unloaded.")

        # Clear runtime state
        state = {"kfuncs_loaded": False, "active_const_ids": {}}
        save_runtime_state(state)
        update_all_status("ready")
    else:
        # Unload specific ConstIDs
        for cid in args:
            if cid not in active:
                print(f"Warning: ConstID {cid} is not active, skipping.")
                continue
            unload_constid(cid)
            update_status(cid, "ready")
            print(f"ConstID {cid} unloaded.")

        # Give BPF time to detach
        time.sleep(1)

        # Refresh state and check if we should unload kfuncs
        state = get_runtime_state()
        if not state.get("active_const_ids"):
            if is_kfuncs_loaded():
                print("No more active ConstIDs. Unloading kfuncs module...")
                result = subprocess.run(['sudo', 'rmmod', 'xk-kfuncs'],
                                        capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Warning: Failed to unload kfuncs: {result.stderr}")
                else:
                    state["kfuncs_loaded"] = False
                    save_runtime_state(state)
                    print("kfuncs module unloaded.")


def cmd_status(args):
    """Show runtime status of loaded ConstIDs."""
    from src.loader import get_runtime_state, is_kfuncs_loaded

    state = get_runtime_state()
    active = state.get("active_const_ids", {})

    kfuncs_loaded = is_kfuncs_loaded()
    print(f"kfuncs module: {'loaded' if kfuncs_loaded else 'not loaded'}")

    if not active:
        print("No active ConstIDs.")
        return

    mode_names = {0: 'Immediate', 1: 'Per-task', 2: 'Global'}
    print(f"Active ConstIDs ({len(active)}):")
    for cid, info in sorted(active.items(), key=lambda x: int(x[0])):
        mode_str = mode_names.get(info.get("mode", -1), "Unknown")
        bpf_file = info.get("bpf_file", "?")
        status = info.get("status", "?")
        print(f"  ConstID {cid}: mode={mode_str}, file={bpf_file}, status={status}")


def _unload_active_constids(const_ids):
    """Unload any active ConstIDs before deleting their table entries.

    Args:
        const_ids: set of ConstID strings to check and unload.

    Returns:
        Number of ConstIDs unloaded.
    """
    from src.loader import unload_constid, get_runtime_state

    state = get_runtime_state()
    active = state.get("active_const_ids", {})
    unloaded = 0

    for cid in sorted(const_ids):
        if str(cid) in active:
            print(f"ConstID {cid} is active — unloading before delete...")
            unload_constid(str(cid))
            update_status(str(cid), "ready")
            unloaded += 1

    return unloaded


def _collect_constids_to_delete(args):
    """Determine which ConstIDs a 'table delete' command would affect.

    Replicates the filter logic in table.py delete_entries() without
    actually modifying any files.

    Returns:
        set of ConstID strings, or None if not a delete command.
    """
    if not args or args[0] != 'delete':
        return None

    delete_all = '--all' in args
    const_id = val = status = None
    i = 1
    while i < len(args):
        if args[i] == '--const-id' and i + 1 < len(args):
            const_id = args[i + 1]; i += 2
        elif args[i] == '--val' and i + 1 < len(args):
            val = args[i + 1]; i += 2
        elif args[i] == '--status' and i + 1 < len(args):
            status = args[i + 1]; i += 2
        elif args[i] == '--all':
            i += 1
        else:
            i += 1

    if not os.path.exists(SCOPE_TABLE):
        return set()

    # Read scope table to find matching ConstIDs
    import csv
    affected = set()
    with open(SCOPE_TABLE, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader, None)
        if not header:
            return set()
        for row in reader:
            if len(row) < 7:
                continue
            entry_cid = row[0].strip()
            entry_val = row[1].strip()
            entry_status = row[6].strip()

            if delete_all:
                affected.add(entry_cid)
                continue

            match = True
            if const_id and entry_cid != const_id:
                match = False
            if val and entry_val != val:
                match = False
            if status and entry_status != status:
                match = False
            if match and (const_id or val or status):
                affected.add(entry_cid)

    return affected


def cmd_table(args):
    """Manage scope tables."""
    # Before delete: unload any active ConstIDs that would be affected
    affected = _collect_constids_to_delete(args)
    if affected:
        _unload_active_constids(affected)

    project_root = get_project_root()
    table_script = os.path.join(project_root, 'src', 'table.py')
    ret = subprocess.run([sys.executable, table_script] + args)
    sys.exit(ret.returncode)


def cmd_trace(args):
    """Trace kernel BPF logs."""
    subprocess.run(['sudo', 'bpftool', 'prog', 'tracelog'])


def show_help():
    """Show help message."""
    print("Usage: xkernel-tool <command> [options]")
    print()
    print("Commands:")
    print("  build     Build tunables from TOML config (or --all for clean rebuild)")
    print("  load      Load BPF kprobes for a single ConstID")
    print("  unload    Unload BPF kprobes (per-ConstID or all)")
    print("  status    Show runtime status of loaded ConstIDs")
    print("  table     Manage scope tables (list, query, delete, cs, ss)")
    print("  trace     Trace the kernel logs")
    print()
    print("Options for 'build':")
    print("  <config.toml>  Build tunables from a TOML config file")
    print("  --all          Clean rebuild: clear tables + build all from tunables/all.toml")
    print("  --skip-gen     Skip running gen.py (only run codegen.py and make)")
    print("  --run-analysis Run SS analysis for missing safe_spans")
    print("  --verbose/-v   Show detailed intermediate output (symbolic execution, diffs)")
    print()
    print("Options for 'load':")
    print("  <MODE>        0=Immediate, 1=Per-task, 2=Global")
    print("  <ConstID>     Single ConstID to load")
    print("  [timeout]     Optional timeout in seconds (for Mode 2)")
    print("  --jump-opt    Try candidate kprobe offsets for JMP optimization")
    print()
    print("Options for 'unload':")
    print("  <ConstID>     Unload a specific ConstID")
    print("  --all         Unload all active ConstIDs and kfuncs module")
    print()
    print("Options for 'table':")
    print("  list                    List all scope table entries")
    print("  query [filters]         Query entries")
    print("  delete [filters|--all]  Delete entries")
    print("  cs [--index N]          Show Critical Span entries")
    print("  ss [--index N]          Show Symbolic State entries")
    print()
    print("Examples:")
    print("  xkernel-tool build tunables/shrink_batch.toml  # Build single tunable")
    print("  xkernel-tool build --all                       # Legacy batch build")
    print("  xkernel-tool load 0 1             # Load ConstID 1 in Immediate mode")
    print("  xkernel-tool load 2 2 5           # Load ConstID 2 in Global mode, 5s timeout")
    print("  xkernel-tool unload 1             # Unload ConstID 1")
    print("  xkernel-tool unload --all         # Unload everything")
    print("  xkernel-tool status               # Show loaded ConstIDs")
    print("  xkernel-tool table list           # List scope table")
    print("  xkernel-tool table delete --all   # Clear all tables")
    sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'build': cmd_build,
        'load': cmd_load,
        'unload': cmd_unload,
        'status': cmd_status,
        'table': cmd_table,
        'trace': cmd_trace,
    }

    if command in commands:
        commands[command](args)
    else:
        show_help()


if __name__ == "__main__":
    main()
