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
DEFAULT_LINUX_PATH = "~/linux-6.14.0-export-symbol"
REQUIRED_TOOLS = ["gcc", "make", "objdump", "sed", "diff", "grep"]  # Added grep
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

def get_file_hash(file_path):
    """Create a safe hash from file path for unique naming"""
    return str(file_path).replace("/", "_").replace(".", "_")

def process_file(kernel_path, build_path, file_path, is_original=True):
    """Process a single file: compile, disassemble, and manage artifacts"""
    rel_path = file_path.relative_to(kernel_path)
    obj_rel_path = rel_path.with_suffix(".o")
    obj_abs_path = kernel_path / obj_rel_path
    file_hash = get_file_hash(rel_path)
    
    dest_obj_file = build_path / f"{file_hash}.o"
    disas_file = build_path / f"{file_hash}_{'original' if is_original else 'recompiled'}.disas.txt"
    orig_obj_file = build_path / f"{file_hash}_{'original' if is_original else 'recompiled'}.orig.o"

    print_color(f"Compiling {rel_path}...", "blue")
    if not run_command(["make", str(obj_rel_path)], cwd=kernel_path):
        raise RuntimeError(f"Compilation failed for {rel_path}")
    
    if obj_abs_path.exists():
        shutil.copy2(str(obj_abs_path), str(orig_obj_file))
        print_color(f"   - Saved original object file to: {orig_obj_file}", "green")
        shutil.move(str(obj_abs_path), str(dest_obj_file))
        print_color(f"   - Moved {obj_abs_path.name} to {build_path}", "green")
    else:
        raise RuntimeError(f"Build artifact {obj_abs_path} not found")

    print_color(f"Generating disassembly for {rel_path}...", "blue")
    objdump_cmd = ["objdump", "-d", str(dest_obj_file)]
    disassembly_content = run_command(objdump_cmd, cwd=kernel_path, capture_output=True)
    if disassembly_content is False:
        raise RuntimeError(f"Disassembly failed for {rel_path}")
    
    with open(disas_file, "w") as f:
        f.write(disassembly_content)
    print_color(f"   - Disassembly saved to: {disas_file}", "green")
    
    return dest_obj_file, disas_file, orig_obj_file

def search_macro_usage(kernel_path, macro_name):
    """Search for files using the specified macro"""
    print_color(f"\nSearching for macro '{macro_name}' in kernel source...", "blue")
    # Use grep to find C files containing the macro (whole word match)
    grep_cmd = [
        "grep", 
        "-rwn", 
        "--include=*.c", 
        "--include=*.h",
        "-e", f"\\b{macro_name}\\b",
        str(kernel_path)
    ]
    
    try:
        result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print_color(f"No files found using macro '{macro_name}'", "yellow")
        return []

    # Parse results and extract unique C files
    files = set()
    for line in result.stdout.splitlines():
        # Extract file path (before first colon)
        file_path = line.split(":")[0]
        if file_path.endswith(".c") or file_path.endswith(".h"):  # Only process C source files or header files
            files.add(Path(file_path))
    
    print_color(f"Found {len(files)} files using macro '{macro_name}':", "green")
    for file in sorted(files):
        print_color(f"   - {file.relative_to(kernel_path)}", "green")
    
    return sorted(files)

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
        description="Automates modification, compilation, disassembly of Linux kernel files.\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-p", "--path",
        default=os.path.expanduser(DEFAULT_LINUX_PATH),
        help=f"Path to the Linux kernel source code.\nDefault: {DEFAULT_LINUX_PATH}"
    )
    parser.add_argument(
        "-f", "--file",
        help="Target C file to operate on (relative to kernel root).\nExample: mm/vmscan.c"
    )
    parser.add_argument(
        "-s", "--sed",
        nargs=2,
        metavar=("<FROM_CODE>", "<TO_CODE>"),
        help="Modify the file using sed.\nRequires two arguments: the pattern to find and the replacement string."
    )
    parser.add_argument(
        "-m", "--macro",
        help="Macro name to search for after modification. Will recompile all files using this macro."
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
    kernel_path = Path(args.path).resolve()

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
    # --- Validate required arguments ---
    if not args.file:
        parser.error("Error: The --file argument is required when not using --clean.")

    # --- Step 1: Environment Check ---
    check_tools()
    source_file = kernel_path / args.file
    build_path = kernel_path / BUILD_DIR_NAME

    print_color("2. Checking paths and files...", "blue")
    if not kernel_path.is_dir():
        print_color(f"Error: Kernel source path '{kernel_path}' does not exist or is not a directory.", "red")
        sys.exit(1)
    
    if not source_file.is_file():
        print_color(f"Error: Source file '{source_file}' does not exist.", "red")
        sys.exit(1)
    
    # Create build directory
    build_path.mkdir(exist_ok=True)
    
    print_color(f"   - Kernel Path: {kernel_path}", "green")
    print_color(f"   - Target File: {source_file}", "green")
    print_color(f"   - Output Dir: {build_path}\n", "green")

    # --- Track files for processing ---
    macro_files = []
    original_disas = {}
    recompiled_disas = {}

    try:
        # --- Step 3: Initial Compilation for Target File ---
        print_color("3. Performing initial compilation for target file...", "blue")
        target_obj, target_orig_disas, target_orig_obj = process_file(
            kernel_path, build_path, source_file, is_original=True
        )
        original_disas[source_file] = target_orig_disas

        # --- Step 4: Find macro-using files (if specified) ---
        if args.macro:
            macro_files = search_macro_usage(kernel_path, args.macro)
            # Process initial compilation for macro files
            for file in macro_files:
                if file != source_file:  # Skip if it's our target file
                    obj, disas, orig_obj = process_file(
                        kernel_path, build_path, file, is_original=True
                    )
                    original_disas[file] = disas

        # --- Step 5: Modify File (if --sed is provided) ---
        if args.sed:
            print_color("\n5. Modifying file using sed...", "blue")
            from_code, to_code = args.sed
            
            # Create backup of original file
            backup_file = build_path / f"{source_file.name}.backup"
            shutil.copy2(str(source_file), str(backup_file))
            print_color(f"   Created backup: {backup_file}", "green")
            
            def macro_to_pattern(line):
                m = re.match(r"^#define\s+(\w+)\s+(.+)$", line)
                if m:
                    macro, value = m.group(1), m.group(2)
                    pattern = rf"#define\s+{re.escape(macro)}\s+{re.escape(value.strip())}"
                    pattern = pattern.replace(r"\s+", r"[ \t]+")
                    return pattern
                return re.escape(line)
            from_pattern = macro_to_pattern(from_code)
            to_code_stripped = to_code.strip()
            from_code_stripped = from_code.strip()
            sed_expr = f"s|{from_pattern}|{to_code_stripped}|g"
            if not run_command(["sed", "-i", "-E", sed_expr, str(source_file)], cwd=kernel_path):
                raise RuntimeError("Failed to modify file using sed.")
            # for future restoring
            sed_expr_for_restoring = f"s|{to_code_stripped}|{from_code_stripped}|g"
            print_color("   File modified successfully.\n", "yellow")

            # --- Step 6: Recompilation for Target File ---
            print_color("6. Recompiling modified target file...", "blue")
            _, target_recomp_disas, target_recomp_obj = process_file(
                kernel_path, build_path, source_file, is_original=False
            )
            recompiled_disas[source_file] = target_recomp_disas

            # --- Step 7: Recompile macro-using files ---
            if args.macro and macro_files:
                print_color("\n7. Recompiling files using specified macro...", "blue")
                for file in macro_files:
                    _, disas, orig_obj = process_file(
                        kernel_path, build_path, file, is_original=False
                    )
                    recompiled_disas[file] = disas

            # --- Step 8: Always perform diff comparison ---
            print_color("\n8. Comparing disassembly results...", "blue")
            for file in original_disas:
                if file in recompiled_disas:
                    print_color(f"\n--- Diff for {file.relative_to(kernel_path)} ---", "yellow")
                    if args.ignore_number_colon:
                        diff = diff_ignore_number_colon(original_disas[file], recompiled_disas[file])
                        if diff:
                            for line in diff:
                                print(line)
                        else:
                            print_color("No differences found", "green")
                    else:
                        diff_cmd = ["diff", str(original_disas[file]), str(recompiled_disas[file]), "-U0"]
                        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
                        if diff_result.stdout:
                            print(diff_result.stdout)
                        else:
                            print_color("No differences found", "green")
            
            # --- Step 9: Restore original file ---
            print_color("\n9. Restoring the original file...", "blue")
            backup_file = build_path / f"{source_file.name}.backup"
            if backup_file.exists():
                # Use backup file for reliable restoration
                shutil.copy2(str(backup_file), str(source_file))
                print_color("   Original file restored from backup successfully.", "green")
                # Clean up backup file
                backup_file.unlink()
                print_color("   Backup file cleaned up.", "green")
            else:
                # Fallback to sed method
                print_color(f"   Backup not found, using sed restore pattern: {sed_expr_for_restoring}", "yellow")
                if not run_command(["sed", "-i", "-E", sed_expr_for_restoring, str(source_file)], cwd=kernel_path):
                    print_color("   Warning: sed restore failed, trying alternative method...", "yellow")
                    # Alternative: use a different delimiter if | is in the content
                    if "|" in to_code_stripped or "|" in from_code_stripped:
                        alt_sed_expr = f"s#{to_code_stripped}#{from_code_stripped}#g"
                        print_color(f"   Trying alternative pattern: {alt_sed_expr}", "yellow")
                        if not run_command(["sed", "-i", "-E", alt_sed_expr, str(source_file)], cwd=kernel_path):
                            raise RuntimeError("Failed to restore the original file with alternative method.")
                    else:
                        raise RuntimeError("Failed to restore the original file.")
                print_color("   Original file restored successfully via sed.", "green")
            print_color("   Original file restored successfully.\n", "green")
        else:
            print_color("Skipping modification, recompilation, and diff steps because --sed was not provided.", "yellow")

        # --- Step 10: Use addr2line to get all source-code lines for the instructions that have changed
        print_color("\n10. Using addr2line to get all source-code lines for the instructions that have changed...", "blue")
        for line in diff_result.stdout.splitlines():
            flag = "+" if args.reverse else "-"
            if line.startswith(flag):
                if len(line.split()) < 2:
                    continue
                offset = line.split()[1]
                obj = target_recomp_obj if args.reverse else target_orig_obj
                addr2line_cmd = ["addr2line", "-e", str(obj), offset]
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
                    print_color("No differences found", "green")

        # --- Step 11: Cleanup intermediate object files ---
        # print_color("\n10. Cleaning up intermediate object files...", "blue")
        # for obj_file in build_path.glob("*.o"):
        #     try:
        #         obj_file.unlink()
        #         print_color(f"   - Removed: {obj_file.name}", "green")
        #     except OSError as e:
        #         print_color(f"   - Error: Failed to remove {obj_file.name}: {e}", "red")

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