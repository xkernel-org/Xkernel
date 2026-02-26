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


def cmd_build(args):
    """Build pipeline: gen -> codegen -> compile."""
    project_root = get_project_root()
    xkernel_dir = os.path.join(project_root, 'xkernel')
    skip_gen = '--skip-gen' in args

    print("==========================================")
    print("Xkernel Build Pipeline")
    print("==========================================")

    # Step 1: Run gen.py
    if not skip_gen:
        print("\n[Step 1/3] Running gen.py to generate Basic Block analysis...")
        print("==========================================")
        from xkernel.gen import generate_bb_files
        generate_bb_files()
    else:
        print("\n[Step 1/3] Skipped gen.py (--skip-gen)")

    # Step 2: Run codegen.py
    print("\n[Step 2/3] Running codegen.py to generate BPF code...")
    print("==========================================")
    from xkernel.codegen import run_codegen
    run_codegen()

    # Step 3: Compile BPF programs
    print("\n[Step 3/3] Compiling BPF programs...")
    print("==========================================")
    bpf_dir = os.path.join(project_root, 'bpf')
    ret = subprocess.run(['make', f'-j{os.cpu_count()}'], cwd=bpf_dir)
    if ret.returncode != 0:
        print("Error: BPF compilation failed")
        sys.exit(1)

    print("\n==========================================")
    print("Build completed successfully!")
    print("==========================================")
    print(f"\nNext steps:")
    print(f"  ./xkernel-tool load <MODE> <ConstID>    # Load the BPF program")
    print(f"  ./xkernel-tool unload                   # Unload when done")


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

    full_path = os.path.join(project_root, 'bpf', 'examples', bpf_file)
    return full_path, bpf_file


def cmd_load(args):
    """Load BPF kprobes for a single ConstID with per-ConstID lifecycle."""
    from xkernel.loader import (
        ensure_kfuncs_loaded, load_and_attach_per_constid,
        load_critical_spans_for_constid, activate_constid,
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

    # Step 1: Generate CS file for this ConstID
    print(f"Generating CS file for ConstID: {const_id}")
    generate_cs_file(const_id)

    # Step 2: Generate cs_artifact and compile BPF
    bpf_dir = os.path.join(project_root, 'bpf')
    cs_artifact_path = os.path.join(bpf_dir, 'cs_artifact.bpf.h')
    generate_cs_artifact_header(CS_FILE, cs_artifact_path)

    print("Compiling BPF files...")
    bpf_c = bpf_o_path.replace('.bpf.o', '.bpf.c')
    obj = compile_single_bpf(bpf_c, bpf_dir)
    if obj is None:
        print(f"Error: Failed to compile {os.path.basename(bpf_c)}")
        sys.exit(1)
    print(f"  Compiled: {os.path.basename(bpf_c)}")

    # Step 3: Jump optimization (optional)
    if jump_opt:
        from xkernel.loader import try_jump_optimization
        print("\n--- Jump Optimization ---")
        print("Probing candidate offsets for jump-optimized kprobes...")
        optimized = try_jump_optimization(bpf_c, bpf_dir)
        if optimized:
            print(f"  Jump optimization applied to {os.path.basename(bpf_c)}")
        else:
            print(f"  No jump-optimizable offsets found in {os.path.basename(bpf_c)}")
        print("--- End Jump Optimization ---\n")

    # Step 4: Ensure kfuncs module is loaded (idempotent)
    if not ensure_kfuncs_loaded(project_root):
        print("Failed to load kfuncs module")
        sys.exit(1)

    # Step 5: Load and attach BPF programs (per-ConstID)
    mode_names = {0: 'Immediate', 1: 'Per-task', 2: 'Global'}
    print(f"Loading BPF for ConstID {const_id} (mode={mode_names[mode]}):")
    print(f"  File: {bpf_o_path}")
    ret, map_info = load_and_attach_per_constid([bpf_o_path], const_id, mode)
    if ret != 0:
        print(f"Failed to load kprobes for ConstID {const_id}.")
        sys.exit(ret)

    # Step 6: Load critical spans
    load_critical_spans_for_constid(CS_FILE, const_id, map_info)

    # Step 7: Mode 2 (Global) — load consistency module, wait, activate
    if mode == 2:
        print("Loading global consistency module for transition...")
        consistency_path = os.path.join(project_root, 'kernel', 'consistency',
                                        'xk-consistency.ko')
        if not os.path.exists(consistency_path):
            print(f"Error: Consistency module not found: {consistency_path}")
            print("Cleaning up loaded BPF programs...")
            from xkernel.loader import unload_constid
            unload_constid(const_id)
            sys.exit(1)

        timeout_val = int(args[2]) if len(args) > 2 else 5

        # Capture dmesg baseline before insmod
        dmesg_before = subprocess.run(
            ['sudo', 'dmesg'], capture_output=True, text=True
        )
        baseline_lines = len(dmesg_before.stdout.splitlines()) if dmesg_before.returncode == 0 else 0

        cmd = ['sudo', 'insmod', consistency_path, f'kTimeout={timeout_val}']
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
            from xkernel.loader import unload_constid
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
                    if '[Transition] Transition done' in line:
                        transition_done = True
                        break
                    if '[Transition] Transition failed' in line:
                        print("Warning: Global transition failed (timeout)")
                        break
                if transition_done or any('[Transition] Transition failed' in l for l in new_lines):
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

    # Show kprobe placement visualization
    try:
        from xkernel.codegen import show_kprobe_placement_from_bpf_file
        show_kprobe_placement_from_bpf_file(const_id, bpf_c, project_root)
    except Exception:
        pass

    print(f"\nConstID {const_id} loaded successfully (mode={mode_names[mode]}).")


def cmd_unload(args):
    """Unload BPF kprobes for specific ConstIDs or all."""
    from xkernel.loader import (
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
    from xkernel.loader import get_runtime_state, is_kfuncs_loaded

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


def cmd_table(args):
    """Manage scope tables."""
    project_root = get_project_root()
    table_script = os.path.join(project_root, 'xkernel', 'table.py')
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
    print("  build     Generate BPF code from tests and compile")
    print("  load      Load BPF kprobes for a single ConstID")
    print("  unload    Unload BPF kprobes (per-ConstID or all)")
    print("  status    Show runtime status of loaded ConstIDs")
    print("  table     Manage scope tables (list, query, delete, cs, ss)")
    print("  trace     Trace the kernel logs")
    print()
    print("Options for 'build':")
    print("  --skip-gen    Skip running gen.py (only run codegen.py and make)")
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
    print("  xkernel-tool build                # Full build pipeline")
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
