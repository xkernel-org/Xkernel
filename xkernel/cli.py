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


def cmd_load(args):
    """Load BPF kprobes for specified ConstIDs or files."""
    # Detect --jump-opt flag
    jump_opt = '--jump-opt' in args
    args = [a for a in args if a != '--jump-opt']

    if len(args) < 2:
        print("Missing argument: [0:Immediate, 1:Per-task, 2:Global] "
              "[ConstID1,ConstID2,...] or [file1,file2,...] [Timeout seconds]")
        sys.exit(1)

    mode = int(args[0])
    if mode not in (0, 1, 2):
        print(f"Invalid mode: {mode}")
        sys.exit(1)

    input_str = args[1]
    project_root = get_project_root()

    resolved_files = []
    loaded_const_ids = []
    loaded_bpf_files = []

    for item in input_str.split(','):
        item = item.strip()
        if re.match(r'^\d+$', item):
            # It's a ConstID
            if not os.path.exists(SCOPE_TABLE):
                print(f"Error: Scope Table not found at {SCOPE_TABLE}")
                sys.exit(1)

            const_id = item
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
                print(f"Error: ConstID {const_id} not found in Scope Table")
                sys.exit(1)

            full_path = os.path.join(project_root, 'bpf', 'examples', bpf_file)
            if not os.path.exists(full_path):
                print(f"Error: BPF file not found: {full_path} (for ConstID {const_id})")
                sys.exit(1)

            resolved_files.append(full_path)
            loaded_const_ids.append(const_id)
        else:
            # It's a file path
            if not os.path.exists(item):
                print(f"Error: File not found: {item}")
                sys.exit(1)
            resolved_files.append(item)
            loaded_bpf_files.append(os.path.basename(item))

    if not resolved_files:
        print("Error: No valid files to load")
        sys.exit(1)

    # Generate CS file if we have ConstIDs
    if loaded_const_ids:
        const_ids_str = ','.join(loaded_const_ids)
        print(f"Generating CS file for ConstIDs: {const_ids_str}")
        generate_cs_file(const_ids_str)

    # Generate cs_artifact and compile only the needed BPF files
    from xkernel.loader import generate_cs_artifact_header, compile_single_bpf

    bpf_dir = os.path.join(project_root, 'bpf')
    cs_artifact_path = os.path.join(bpf_dir, 'cs_artifact.bpf.h')
    generate_cs_artifact_header(CS_FILE, cs_artifact_path)

    print("Compiling BPF files...")
    for bpf_file in resolved_files:
        bpf_c = bpf_file.replace('.bpf.o', '.bpf.c')
        if os.path.exists(bpf_c):
            obj = compile_single_bpf(bpf_c, bpf_dir)
            if obj is None:
                print(f"Error: Failed to compile {os.path.basename(bpf_c)}")
                sys.exit(1)
            print(f"  Compiled: {os.path.basename(bpf_c)}")
        else:
            print(f"Warning: Source not found: {bpf_c}")

    # Jump optimization: try candidate offsets to find jump-optimized kprobes
    if jump_opt:
        from xkernel.loader import try_jump_optimization
        print("\n--- Jump Optimization ---")
        print("Probing candidate offsets for jump-optimized kprobes...")
        for bpf_file in resolved_files:
            bpf_c = bpf_file.replace('.bpf.o', '.bpf.c')
            if os.path.exists(bpf_c):
                optimized = try_jump_optimization(bpf_c, bpf_dir)
                if optimized:
                    print(f"  Jump optimization applied to {os.path.basename(bpf_c)}")
                else:
                    print(f"  No jump-optimizable offsets found in {os.path.basename(bpf_c)}")
        print("--- End Jump Optimization ---\n")

    # Load kernel module
    print("Loading kfuncs module...")
    kfuncs_path = os.path.join(project_root, 'kernel', 'kfuncs', 'xk-kfuncs.ko')
    ret = subprocess.run(['sudo', 'insmod', kfuncs_path, f'kMode={mode}'])
    if ret.returncode != 0:
        print("Failed to load kfuncs module")
        sys.exit(1)

    # Load and attach BPF programs
    from xkernel.loader import load_and_attach, load_critical_spans

    print("Loading BPF Kprobes:")
    print(f"  Files: {','.join(resolved_files)}")
    ret = load_and_attach(resolved_files, pin=True)
    if ret != 0:
        print("Failed to load kprobes. You can try xkernel-tool unload and load again.")
        sys.exit(ret)

    # Load critical spans
    load_critical_spans(CS_FILE)

    # Update status
    for cid in loaded_const_ids:
        update_status(cid, "active")
    for bpf in loaded_bpf_files:
        update_status_by_file(bpf, "active")

    # Load global consistency module if mode 2
    if mode == 2:
        print("Loading global consistency module for transition...")
        consistency_path = os.path.join(project_root, 'kernel', 'consistency',
                                        'xk-consistency.ko')
        cmd = ['sudo', 'insmod', consistency_path]
        if len(args) > 2:
            timeout = args[2]
            cmd.append(f'kTimeout={timeout}')
        subprocess.run(cmd)
        print("Check dmesg to see if the transition is successful.")


def cmd_unload(args):
    """Unload all loaded BPF kprobes."""
    print("Unloading global consistency module for transition (if loaded)...")
    subprocess.run(['sudo', 'rmmod', 'xk-consistency'],
                   capture_output=True)

    print("Unloading BPF Kprobes...")
    subprocess.run(['sudo', 'rm', '-rf', '/sys/fs/bpf/xkernel'],
                   capture_output=True)

    # Give BPF tools time to detach
    time.sleep(2)
    print("Unloading kfuncs module...")
    subprocess.run(['sudo', 'rmmod', 'xk-kfuncs'])

    # Update status
    update_all_status("ready")

    print("Check dmesg to see if the transition is successful.")


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
    print("  load      Load BPF kprobes for specified ConstIDs or files")
    print("  unload    Unload all loaded BPF kprobes")
    print("  table     Manage scope tables (list, query, delete, cs, ss)")
    print("  trace     Trace the kernel logs")
    print()
    print("Options for 'build':")
    print("  --skip-gen    Skip running gen.py (only run codegen.py and make)")
    print()
    print("Options for 'load':")
    print("  <MODE>        0=Immediate, 1=Per-task, 2=Global")
    print("  <IDs/files>   ConstIDs (e.g., 1,2) or BPF file paths")
    print("  [timeout]     Optional timeout in seconds (for Mode 2)")
    print("  --jump-opt    Try candidate kprobe offsets for JMP optimization")
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
    print("  xkernel-tool table list           # List scope table")
    print("  xkernel-tool table delete --all   # Clear all tables")
    print("  xkernel-tool unload               # Unload all kprobes")
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
        'table': cmd_table,
        'trace': cmd_trace,
    }

    if command in commands:
        commands[command](args)
    else:
        show_help()


if __name__ == "__main__":
    main()
