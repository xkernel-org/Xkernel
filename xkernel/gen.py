#!/usr/bin/env python3
"""Basic Block generation script.

Reads testcases from xkernel.testcases, runs diff.py commands,
and extracts Basic Block output into *_bb_v1.txt, *_bb_v2.txt, *_bb_v3.txt files.

Replaces the old codegen/gen.sh.
"""

import os
import re
import shutil
import subprocess
import sys


def strip_ansi(text):
    """Remove ANSI escape sequences from text."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def extract_step11(output):
    """Extract step 11 (original) output from check_assembly_diff.py output."""
    lines = output.split('\n')
    result = []
    in_step11 = False
    for line in lines:
        if re.match(r'^11\. Extracting Basic Blocks for changed instructions\.\.\.', line):
            in_step11 = True
            continue
        if in_step11:
            if re.match(r'^11b\.', line) or re.match(r'^12\.', line) or \
               line.startswith('Script finished successfully.') or \
               line.startswith('All disassembly files saved to'):
                break
            # Skip "Instruction at..." lines
            if re.match(r'^Instruction at 0x.*found at line', line):
                continue
            result.append(line)
    return '\n'.join(result).strip()


def extract_step11b(output):
    """Extract step 11b (recompiled) output from check_assembly_diff.py output."""
    lines = output.split('\n')
    result = []
    in_step11b = False
    for line in lines:
        if re.match(r'^11b\.', line):
            in_step11b = True
            continue
        if in_step11b:
            if re.match(r'^12\.', line) or \
               line.startswith('Script finished successfully.') or \
               line.startswith('All disassembly files saved to'):
                break
            if re.match(r'^Instruction at 0x.*found at line', line):
                continue
            result.append(line)
    return '\n'.join(result).strip()


def build_diff_command(file, original, modified, lines=None):
    """Build a diff.py command as an argv list (no shell=True needed).

    Args:
        file: kernel source file path (e.g. "net/ipv4/tcp_cubic.c")
        original: original source expression
        modified: replacement expression
        lines: optional --lines filter string

    Returns:
        list of command arguments for subprocess.run()
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = ['sudo', sys.executable, os.path.join(script_dir, 'diff.py'),
           '-f', file, '-s', original, modified]
    if lines:
        cmd.extend(['--lines', lines])
    return cmd


def generate_bb_files():
    """Generate BB files for all testcases.

    Returns:
        list of (test_num, v1_file, v2_file, v3_file) tuples for files written.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    from xkernel.testcases import TESTCASES

    # Use a dedicated subdirectory for BB files; clear it to avoid stale files
    bb_dir = os.path.join(script_dir, 'bb_cache')
    if os.path.exists(bb_dir):
        shutil.rmtree(bb_dir)
    os.makedirs(bb_dir)

    results = []

    for test_num, tc in enumerate(TESTCASES, 1):
        cmd1 = build_diff_command(tc.file, tc.original, tc.modified[0], tc.lines)
        cmd2 = build_diff_command(tc.file, tc.original, tc.modified[1], tc.lines)

        v1_file = os.path.join(bb_dir, f'{test_num}_bb_v1.txt')
        v2_file = os.path.join(bb_dir, f'{test_num}_bb_v2.txt')
        v3_file = os.path.join(bb_dir, f'{test_num}_bb_v3.txt')

        print(f"Processing TEST GROUP {test_num}...")
        print(f"  Command 1: {' '.join(cmd1)}")
        print(f"  Command 2: {' '.join(cmd2)}")

        # Execute first command
        print("  -> Executing command 1...")
        try:
            result1 = subprocess.run(
                cmd1, capture_output=True, text=True,
                cwd=project_root, env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            output1 = strip_ansi(result1.stdout + result1.stderr)
        except Exception as e:
            print(f"  -> Error: Command 1 failed: {e}")
            for f in [v1_file, v2_file, v3_file]:
                with open(f, 'w') as fh:
                    fh.write(f"# Command 1 failed: {' '.join(cmd1)}\n")
            continue

        if result1.returncode != 0:
            print(f"  -> Error: Command 1 failed with exit code {result1.returncode}")
            for f in [v1_file, v2_file, v3_file]:
                with open(f, 'w') as fh:
                    fh.write(f"# Command 1 failed: {' '.join(cmd1)}\n")
            continue

        # Extract step 11 -> v1
        step11 = extract_step11(output1)
        if step11:
            with open(v1_file, 'w') as f:
                f.write(step11 + '\n')
            print(f"    -> Step 11 (original) written to {v1_file}")
        else:
            print("    -> Warning: No step 11 output found for v1")
            with open(v1_file, 'w') as f:
                f.write("# No step 11 output found\n")

        # Extract step 11b -> v2
        step11b = extract_step11b(output1)
        if step11b:
            with open(v2_file, 'w') as f:
                f.write(step11b + '\n')
            print(f"    -> Step 11b (recompiled) from command 1 written to {v2_file}")
        else:
            print("    -> Warning: No step 11b output found for v2")
            with open(v2_file, 'w') as f:
                f.write("# No step 11b output found\n")

        # Execute second command
        print("  -> Executing command 2...")
        try:
            result2 = subprocess.run(
                cmd2, capture_output=True, text=True,
                cwd=project_root, env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            output2 = strip_ansi(result2.stdout + result2.stderr)
        except Exception as e:
            print(f"  -> Error: Command 2 failed: {e}")
            with open(v3_file, 'w') as f:
                f.write(f"# Command 2 failed: {' '.join(cmd2)}\n")
            continue

        if result2.returncode != 0:
            print(f"  -> Error: Command 2 failed with exit code {result2.returncode}")
            with open(v3_file, 'w') as f:
                f.write(f"# Command 2 failed: {' '.join(cmd2)}\n")
            continue

        # Extract step 11b -> v3
        step11b2 = extract_step11b(output2)
        if step11b2:
            with open(v3_file, 'w') as f:
                f.write(step11b2 + '\n')
            print(f"    -> Step 11b (recompiled) from command 2 written to {v3_file}")
        else:
            print("    -> Warning: No step 11b output found for v3")
            with open(v3_file, 'w') as f:
                f.write("# No step 11b output found\n")

        results.append((test_num, v1_file, v2_file, v3_file))
        print()

    print("Done processing all test groups.")
    return results


def main():
    generate_bb_files()


if __name__ == "__main__":
    main()
