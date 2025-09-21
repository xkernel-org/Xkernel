#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
import re

# --- Configuration ---
REQUIRED_TOOLS = ["objdump", "diff", "addr2line"]  # Only tools needed for comparison
BUILD_DIR_NAME = "BUILDO"  # Directory for all output files

def print_color(text, color="green"):
    """Prints colored text to the terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def check_tools():
    """Checks if the required toolchain is present."""
    print_color("1. Checking for required toolchain...", "blue")
    all_found = True
    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            print_color(f"   - Error: Command '{tool}' not found. Please ensure it is installed and in your system's PATH.", "red")
            all_found = False
        else:
            print_color(f"   - Found: {tool}", "green")
    if not all_found:
        sys.exit(1)
    print_color("   All tools found.\n", "green")


def run_command(command, cwd, capture_output=False):
    """Executes a shell command and handles errors."""
    print_color(f"--> Executing: {' '.join(command)}", "yellow")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=capture_output,
            text=True
        )
        if capture_output:
            return result.stdout
        return True
    except FileNotFoundError:
        print_color(f"Error: Command '{command[0]}' not found.", "red")
        return False
    except subprocess.CalledProcessError as e:
        print_color(f"Error: Command '{' '.join(command)}' failed to execute.", "red")
        print_color(f"Return code: {e.returncode}", "red")
        if e.stdout:
            print(f"--- STDOUT ---\n{e.stdout}")
        if e.stderr:
            print(f"--- STDERR ---\n{e.stderr}")
        return False


def strip_leading_number_colon(line):
    """Remove leading numbers followed by a colon (e.g., '3833:') from a line."""
    return re.sub(r'^\s*\d+:\s*', '', line)

def diff_ignore_number_colon(file1, file2):
    """Diff two files, ignoring lines that only differ by leading numbers and colon."""
    with open(file1, "r") as f1, open(file2, "r") as f2:
        lines1 = [strip_leading_number_colon(l.rstrip('\n')) for l in f1]
        lines2 = [strip_leading_number_colon(l.rstrip('\n')) for l in f2]
    import difflib
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=str(file1), tofile=str(file2), lineterm=''))
    return diff

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Compare two object files and analyze disassembly differences.\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "pre_o",
        help="Path to the pre-modification object file (.o)"
    )
    parser.add_argument(
        "post_o", 
        help="Path to the post-modification object file (.o)"
    )
    parser.add_argument(
        "-i", "--ignore-number-colon",
        action="store_true",
        help="Ignore differences that are only leading numbers followed by a colon (e.g., '3833:') in diff output."
    )
    parser.add_argument(
        "-l", "--lines",
        help="Lines to print when using addr2line. Format: <start_line>-<end_line>,<line>,<start_line>-<end_line>"
    )
    parser.add_argument(
        "-r", "--reverse",
        action="store_true",
        help="Check diff against the post-modification object file."
    )
    args = parser.parse_args()

    if args.lines:
        # Parse args.lines to support formats like xxx-xxx,xxx,xxx-xxx,xxx
        line_set = set()
        for part in args.lines.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start = int(start)
                    end = int(end)
                    if start > end:
                        start, end = end, start
                    line_set.update(range(start, end + 1))
                except ValueError:
                    continue  # skip invalid range
            else:
                try:
                    line_set.add(int(part))
                except ValueError:
                    continue  # skip invalid single line
        args.lines = sorted(line_set)

    # --- Step 1: Environment Check ---
    check_tools()
    
    # Convert to Path objects
    pre_o_path = Path(args.pre_o).resolve()
    post_o_path = Path(args.post_o).resolve()
    
    # Create build directory for output files
    build_path = Path("BUILDO")
    build_path.mkdir(exist_ok=True)

    print_color("2. Checking object files...", "blue")
    if not pre_o_path.is_file():
        print_color(f"Error: Pre-modification object file '{pre_o_path}' does not exist.", "red")
        sys.exit(1)
    
    if not post_o_path.is_file():
        print_color(f"Error: Post-modification object file '{post_o_path}' does not exist.", "red")
        sys.exit(1)
    
    print_color(f"   - Pre-modification object: {pre_o_path}", "green")
    print_color(f"   - Post-modification object: {post_o_path}", "green")
    print_color(f"   - Output Dir: {build_path}\n", "green")

    try:
        # --- Step 3: Generate disassembly for both object files ---
        print_color("3. Generating disassembly for object files...", "blue")
        
        # Generate disassembly for pre-modification object
        pre_disas_file = build_path / "pre.disas.txt"
        print_color(f"Generating disassembly for {pre_o_path.name}...", "blue")
        objdump_cmd = ["objdump", "-d", str(pre_o_path)]
        pre_disassembly = run_command(objdump_cmd, cwd=Path.cwd(), capture_output=True)
        if pre_disassembly is False:
            raise RuntimeError(f"Disassembly failed for {pre_o_path}")
        
        with open(pre_disas_file, "w") as f:
            f.write(pre_disassembly)
        print_color(f"   - Pre-modification disassembly saved to: {pre_disas_file}", "green")
        
        # Generate disassembly for post-modification object
        post_disas_file = build_path / "post.disas.txt"
        print_color(f"Generating disassembly for {post_o_path.name}...", "blue")
        objdump_cmd = ["objdump", "-d", str(post_o_path)]
        post_disassembly = run_command(objdump_cmd, cwd=Path.cwd(), capture_output=True)
        if post_disassembly is False:
            raise RuntimeError(f"Disassembly failed for {post_o_path}")
        
        with open(post_disas_file, "w") as f:
            f.write(post_disassembly)
        print_color(f"   - Post-modification disassembly saved to: {post_disas_file}", "green")

        # --- Step 4: Compare disassembly results ---
        print_color("\n4. Comparing disassembly results...", "blue")
        print_color(f"\n--- Diff between {pre_o_path.name} and {post_o_path.name} ---", "yellow")
        
        if args.ignore_number_colon:
            diff = diff_ignore_number_colon(pre_disas_file, post_disas_file)
            if diff:
                for line in diff:
                    print(line)
            else:
                print_color("No differences found", "green")
        else:
            diff_cmd = ["diff", "-u", str(pre_disas_file), str(post_disas_file)]
            diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
            if diff_result.stdout:
                print(diff_result.stdout)
            else:
                print_color("No differences found", "green")

        # --- Step 5: Use addr2line to get source-code lines for changed instructions ---
        if diff_result.stdout:
            print_color("\n5. Using addr2line to get source-code lines for changed instructions...", "blue")
            flag = "+" if args.reverse else "-"
            o_path = post_o_path if args.reverse else pre_o_path
            for line in diff_result.stdout.splitlines():
                if line.startswith(flag):
                    if len(line.split()) < 2:
                        continue
                    offset = line.split()[1]
                    addr2line_cmd = ["addr2line", "-e", str(o_path), offset]
                    result = subprocess.run(addr2line_cmd, capture_output=True, text=True)
                    if result.stdout:
                        if args.lines:
                            line_number = result.stdout.split(":")[1]
                            line_number = line_number.split(" ")[0]
                            line_number = line_number.rstrip("\n")
                            try:
                                line_number = int(line_number)
                            except ValueError:
                                continue
                            if line_number in args.lines:
                                print(line+"\t"+result.stdout, end="")
                        else:
                            print(line+"\t"+result.stdout, end="")
        else:
            print_color("\n5. No differences found, skipping addr2line analysis.", "green")

    except (RuntimeError, KeyboardInterrupt) as e:
        if isinstance(e, RuntimeError):
            print_color(f"\nScript execution failed: {e}", "red")
        else:
            print_color("\nExecution interrupted by user.", "yellow")
        sys.exit(1)

    print_color("\nScript finished successfully.", "blue")
    print_color(f"All disassembly files saved to: {build_path}", "green")


if __name__ == "__main__":
    main()