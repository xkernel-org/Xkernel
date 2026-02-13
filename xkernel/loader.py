#!/usr/bin/env python3
"""BPF program loader for Xkernel.

Replaces the C++ kprobe_loader with Python + bpftool.
Handles:
  - cs_artifact.bpf.h generation
  - BPF program compilation
  - BPF program loading/attaching/pinning via bpftool
  - Critical span map population
"""

import os
import re
import struct
import subprocess
import sys
import time


CS_PATH = "/dev/shm/xkernel/cs"


def generate_cs_artifact_header(cs_path, output_path):
    """Generate cs_artifact.bpf.h from critical spans file.

    Args:
        cs_path: Path to CS file (format: function_name,address,soff,eoff per line)
        output_path: Path to write the BPF header
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(cs_path):
        # Write empty header
        with open(output_path, 'w') as f:
            f.write("// Empty cs_artifact.bpf.h - no critical spans defined\n")
            f.write("#ifndef __CS_ARTIFACT_BPF_H__\n")
            f.write("#define __CS_ARTIFACT_BPF_H__\n")
            f.write("#endif\n")
        print(f"CS file {cs_path} does not exist, created empty {output_path}",
              file=sys.stderr)
        return

    # Check if CS file has content
    with open(cs_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        with open(output_path, 'w') as f:
            f.write("// Empty cs_artifact.bpf.h - no critical spans defined\n")
            f.write("#ifndef __CS_ARTIFACT_BPF_H__\n")
            f.write("#define __CS_ARTIFACT_BPF_H__\n")
            f.write("#endif\n")
        print(f"CS file {cs_path} is empty, created empty {output_path}",
              file=sys.stderr)
        return

    # Parse CS entries
    cs_entries = []
    for line in lines:
        parts = line.split(',')
        if len(parts) < 4:
            print(f"Malformed line in {cs_path}: {line}", file=sys.stderr)
            continue
        func_name = parts[0]
        soff = int(parts[2], 16)
        cs_entries.append((func_name, soff))

    # Generate BPF header
    with open(output_path, 'w') as f:
        f.write("#ifndef __CS_ARTIFACT_BPF_H__\n")
        f.write("#define __CS_ARTIFACT_BPF_H__\n\n")
        f.write("#include <bpf/bpf_helpers.h>\n")
        f.write("#include <bpf/bpf_tracing.h>\n\n")
        f.write('#include "xkernel.bpf.h"\n\n')

        for func_name, soff in cs_entries:
            if soff == 0:
                sec_name = f"kprobe/{func_name}"
                bpf_func_name = func_name
            else:
                sec_name = f"kprobe/{func_name}+0x{soff:x}"
                bpf_func_name = f"{func_name}_{soff:x}"

            f.write(f'SEC("{sec_name}")\n')
            f.write(f'int BPF_KPROBE({bpf_func_name}) {{\n')
            f.write('    per_task_transition_handler(ctx);\n')
            f.write('    return 0;\n')
            f.write('}\n\n')

        f.write("#endif\n")

    file_size = os.path.getsize(output_path)
    print(f"Generated {output_path} ({file_size} bytes, {len(cs_entries)} entries)",
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
    # cs_len is u64
    val_bytes = struct.pack('<Q', cs_len)
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
