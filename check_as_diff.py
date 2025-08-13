#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
DEFAULT_LINUX_PATH = "~/linux-6.14.0-export-symbol"
REQUIRED_TOOLS = ["gcc", "make", "objdump", "sed", "diff"]
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

def do_clean(kernel_path, build_dir_name, target_to_clean):
    """Cleans up specified artifacts in the BUILDO directory."""
    print_color("--- Starting Clean Task ---", "blue")
    build_path = kernel_path / build_dir_name
    
    # Extract the base name (stem) from the .c or .o file
    target_stem = Path(target_to_clean).stem

    files_to_delete = [
        build_path / f"{target_stem}.o",
        build_path / f"{target_stem}_original.disas.txt",
        build_path / f"{target_stem}_recompiled.disas.txt"
    ]

    if not build_path.is_dir():
        print_color(f"Output directory '{build_path}' does not exist, nothing to clean.", "yellow")
        sys.exit(0)

    print_color(f"Searching for and deleting files related to '{target_stem}' in '{build_path}':", "yellow")
    deleted_count = 0
    for f in files_to_delete:
        if f.exists():
            try:
                f.unlink()
                print_color(f"  - Deleted: {f}", "green")
                deleted_count += 1
            except OSError as e:
                print_color(f"  - Error: Failed to delete {f}: {e}", "red")
        else:
            print_color(f"  - Not found: {f}", "yellow")
    
    if deleted_count == 0:
        print_color("\nNo relevant files found to clean.", "green")
    else:
        print_color("\nClean task finished.", "blue")
    
    sys.exit(0)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Automates modification, compilation, disassembly, and cleanup of Linux kernel files.\n"
                    "Warning: 'sed' modifications are permanent. This script does not automatically clean up generated files unless --clean is used.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-p", "--path",
        default=os.path.expanduser(DEFAULT_LINUX_PATH),
        help=f"Path to the Linux kernel source code.\nDefault: {DEFAULT_LINUX_PATH}"
    )
    parser.add_argument(
        "-f", "--file",
        help="Target C file to operate on (relative to kernel root).\nExample: mm/vmscan.c\n(Required when not using --clean)"
    )
    parser.add_argument(
        "-s", "--sed",
        nargs=2,
        metavar=("<FROM_CODE>", "<TO_CODE>"),
        help="Modify the file using sed.\nRequires two arguments: the pattern to find and the replacement string."
    )
    parser.add_argument(
        "-d", "--diff",
        action="store_true",
        help="If set, performs a diff on the disassembly results at the end."
    )
    parser.add_argument(
        "-c", "--clean",
        metavar="<TARGET>",
        help="Cleans up artifacts for a specific target in the BUILDO directory.\nThis option runs independently and skips the build process.\nExample: mm/vmscan.c or mm/vmscan.o"
    )
    args = parser.parse_args()
    kernel_path = Path(args.path)

    # --- Task Dispatch: If it's a clean task, execute and exit ---
    if args.clean:
        do_clean(kernel_path, BUILD_DIR_NAME, args.clean)
        sys.exit(0)

    # --- If not a clean task, the --file argument is required ---
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

    # --- Preparations ---
    source_object_file_rel_path = Path(args.file).with_suffix(".o")
    source_object_file_abs_path = kernel_path / source_object_file_rel_path
    dest_object_file = build_path / source_object_file_rel_path.name
    original_disas_file = build_path / f"{source_file.stem}_original.disas.txt"
    recompiled_disas_file = build_path / f"{source_file.stem}_recompiled.disas.txt"

    # --- Core Workflow ---
    try:
        # --- Step 3: Initial Compilation ---
        print_color("3. Performing initial compilation...", "blue")
        if not run_command(["make", str(source_object_file_rel_path)], cwd=kernel_path):
            raise RuntimeError("Initial compilation failed.")
        
        if source_object_file_abs_path.exists():
            shutil.move(str(source_object_file_abs_path), str(dest_object_file))
            print_color(f"   - Moved {source_object_file_abs_path.name} to {build_path}", "green")
        else:
            raise RuntimeError(f"Build artifact {source_object_file_abs_path} not found.")
        print_color("   Initial compilation successful.\n", "green")

        # --- Step 4: Initial Disassembly ---
        print_color("4. Performing initial disassembly...", "blue")
        objdump_cmd = ["objdump", "-d", str(dest_object_file)]
        disassembly_content = run_command(objdump_cmd, cwd=kernel_path, capture_output=True)
        if disassembly_content is False:
            raise RuntimeError("Initial disassembly failed.")
        
        with open(original_disas_file, "w") as f:
            f.write(disassembly_content)
        print_color(f"   - Disassembly result saved to: {original_disas_file}\n", "green")

        # --- Step 5: Modify File (if --sed is provided) ---
        if args.sed:
            print_color("5. Modifying file using sed...", "blue")
            from_code, to_code = args.sed
            sed_expr = f"s|{from_code}|{to_code}|g"
            if not run_command(["sed", "-i", sed_expr, str(source_file)], cwd=kernel_path):
                raise RuntimeError("Failed to modify file using sed.")
            print_color("   File modified successfully (Note: This change is permanent).\n", "yellow")

            # --- Step 6: Recompilation ---
            print_color("6. Recompiling modified file...", "blue")
            if not run_command(["make", str(source_object_file_rel_path)], cwd=kernel_path):
                raise RuntimeError("Recompilation failed.")
            
            if source_object_file_abs_path.exists():
                shutil.move(str(source_object_file_abs_path), str(dest_object_file))
                print_color(f"   - Moved {source_object_file_abs_path.name} to {build_path}", "green")
            else:
                raise RuntimeError(f"Build artifact {source_object_file_abs_path} not found.")
            print_color("   Recompilation successful.\n", "green")

            # --- Step 7: Second Disassembly ---
            print_color("7. Performing second disassembly...", "blue")
            re_disassembly_content = run_command(objdump_cmd, cwd=kernel_path, capture_output=True)
            if re_disassembly_content is False:
                raise RuntimeError("Second disassembly failed.")

            with open(recompiled_disas_file, "w") as f:
                f.write(re_disassembly_content)
            print_color(f"   - New disassembly result saved to: {recompiled_disas_file}\n", "green")

            # --- Step 8: Compare Results (if --diff is provided) ---
            if args.diff:
                print_color("8. Comparing disassembly results...", "blue")
                diff_cmd = ["diff", "-u", str(original_disas_file), str(recompiled_disas_file)]
                result = subprocess.run(diff_cmd, cwd=kernel_path, capture_output=True, text=True)
                if result.stdout:
                    print_color("--- Diff Result (Differences found) ---", "yellow")
                    print(result.stdout)
                else:
                    print_color("--- Diff Result (No differences) ---", "green")
            
            # --- Step 9: Use sed to restore the original file ---
            print_color("9. Restoring the original file...", "blue")
            sed_expr = f"s|{to_code}|{from_code}|g"
            if not run_command(["sed", "-i", sed_expr, str(source_file)], cwd=kernel_path):
                raise RuntimeError("Failed to restore the original file.")
            print_color("   Original file restored successfully.\n", "green")
        else:
            print_color("Skipping modification, recompilation, and diff steps because --sed was not provided.", "yellow")
        
        # --- Step 10: Final Cleanup ---
        # [NEW] Delete the final .o file, keeping only the disassembly text files.
        print_color("\n9. Cleaning up intermediate object file...", "blue")
        try:
            if dest_object_file.exists():
                dest_object_file.unlink()
                print_color(f"   - Removed: {dest_object_file}", "green")
            else:
                # This case should not happen in a normal run
                print_color(f"   - Warning: Object file {dest_object_file} not found for cleanup.", "yellow")
        except OSError as e:
            print_color(f"   - Error: Failed to remove object file: {e}", "red")

    except (RuntimeError, KeyboardInterrupt) as e:
        if isinstance(e, RuntimeError):
            print_color(f"\nScript execution failed: {e}", "red")
        else:
            print_color("\nExecution interrupted by user.", "yellow")
        sys.exit(1)

    print_color("\nScript finished.", "blue")
    # [MODIFIED] Updated the final message to reflect the cleanup.


if __name__ == "__main__":
    main()