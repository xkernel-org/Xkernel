#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
DEFAULT_LINUX_PATH = "~/linux-6.14.0-xkernel"
REQUIRED_TOOLS = ["gcc", "make", "objdump", "sed", "diff", "grep"]
BUILD_DIR_NAME = "BUILDO"


# ============================================================================
# Utility Functions
# ============================================================================

def print_color(text, color="green"):
    """Print colored text to the terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")


def check_tools():
    """Check if the required toolchain is present."""
    print_color("1. Checking for required toolchain...", "blue")
    all_found = True
    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            print_color(
                f"   - Error: Command '{tool}' not found. "
                f"Please ensure it is installed and in your system's PATH.",
                "red"
            )
            all_found = False
        else:
            print_color(f"   - Found: {tool}", "green")
    if not all_found:
        sys.exit(1)
    print_color("   All tools found.\n", "green")


def run_command(command, cwd, capture_output=False):
    """Execute a shell command and handle errors."""
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
        print_color(
            f"Error: Command '{' '.join(command)}' failed to execute.",
            "red"
        )
        print_color(f"Return code: {e.returncode}", "red")
        if e.stdout:
            print(f"--- STDOUT ---\n{e.stdout}")
        if e.stderr:
            print(f"--- STDERR ---\n{e.stderr}")
        return False


# ============================================================================
# Vmlinux Functions
# ============================================================================

def build_vmlinux(kernel_path, build_path, is_original=True):
    """Build the entire vmlinux and save it."""
    vmlinux_path = kernel_path / "vmlinux"
    suffix = "original" if is_original else "recompiled"
    dest_vmlinux = build_path / f"vmlinux_{suffix}"

    print_color(f"Building vmlinux ({suffix})...", "blue")
    # Use parallel build
    nproc = os.cpu_count() or 4
    if not run_command(["make", f"-j{nproc}", "vmlinux"], cwd=kernel_path):
        raise RuntimeError("vmlinux build failed")

    shutil.copy2(str(vmlinux_path), str(dest_vmlinux))
    print_color(f"   - Saved vmlinux to: {dest_vmlinux}", "green")
    return dest_vmlinux


def disassemble_function_from_vmlinux(vmlinux_path, build_path, func_name, suffix):
    """Disassemble a specific function from vmlinux."""
    disas_file = build_path / f"vmlinux_{func_name}_{suffix}.disas.txt"

    # Use objdump --disassemble=<func> for function-specific disassembly
    objdump_cmd = ["objdump", "-d", f"--disassemble={func_name}", str(vmlinux_path)]
    disassembly_content = run_command(objdump_cmd, cwd=build_path, capture_output=True)

    if disassembly_content is False:
        raise RuntimeError(f"Disassembly failed for {func_name}")

    with open(disas_file, "w") as f:
        f.write(disassembly_content)

    print_color(f"   - Function {func_name} disassembly saved to: {disas_file}", "green")
    return disas_file


def detect_affected_functions_from_diff(diff_result, original_disas_file):
    """Extract function names from diff result.

    Parses the diff output to find changed addresses, then maps them to function names.
    """
    functions = set()
    if not diff_result or not hasattr(diff_result, 'stdout') or not diff_result.stdout:
        return functions

    # Parse diff to find changed addresses
    changed_addresses = []
    for line in diff_result.stdout.splitlines():
        if line.startswith('-') or line.startswith('+'):
            # Skip header lines
            if line.startswith('---') or line.startswith('+++'):
                continue
            addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
            if addr_match:
                changed_addresses.append(addr_match.group(1))

    # Find functions for these addresses
    for addr in changed_addresses:
        func_info = find_function_for_address_in_file(original_disas_file, addr)
        if func_info:
            functions.add(func_info[0])  # func_info[0] is function name

    return functions


def extract_function_start_from_vmlinux_disas(disas_file, func_name):
    """Extract function start address from vmlinux disassembly file.

    Returns the function start address as integer, or None if not found.
    """
    with open(disas_file, 'r') as f:
        for line in f:
            # Match: "ffffffff821c2ae0 <cubictcp_acked>:"
            match = re.match(r'^([0-9a-fA-F]+)\s+<' + re.escape(func_name) + r'>:', line)
            if match:
                return int(match.group(1), 16)
    return None


def parse_vmlinux_diff_with_offsets(filtered_diff, original_disas_file, func_name):
    """Parse vmlinux diff and extract changed instructions with proper offsets.

    Returns list of tuples: (offset_hex, instruction_line, is_original)
    """
    func_start = extract_function_start_from_vmlinux_disas(original_disas_file, func_name)
    if func_start is None:
        return []

    results = []
    for line in filtered_diff:
        if line.startswith('-') and not line.startswith('---'):
            # Match: -ffffffff821c2cd2: or -  e1:
            addr_match = re.search(r'^-\s*([0-9a-fA-F]+):', line)
            if addr_match:
                addr = int(addr_match.group(1), 16)
                offset = addr - func_start
                results.append((f"0x{offset:x}", line.strip(), True))
        elif line.startswith('+') and not line.startswith('+++'):
            # Match: +ffffffff821c2cd2: or +  e1:
            addr_match = re.search(r'^\+\s*([0-9a-fA-F]+):', line)
            if addr_match:
                addr = int(addr_match.group(1), 16)
                offset = addr - func_start
                results.append((f"0x{offset:x}", line.strip(), False))

    return results


def find_next_instruction_offset(disas_file, func_name, changed_offset):
    """Find the offset of the next instruction after the changed one.

    This is needed for kprobe attachment point.
    """
    func_start = extract_function_start_from_vmlinux_disas(disas_file, func_name)
    if func_start is None:
        return None

    changed_addr = func_start + changed_offset
    found_changed = False

    with open(disas_file, 'r') as f:
        for line in f:
            match = re.match(r'^\s*([0-9a-fA-F]+):\s+', line)
            if match:
                addr = int(match.group(1), 16)
                if found_changed:
                    # This is the next instruction
                    return addr - func_start
                if addr == changed_addr:
                    found_changed = True

    return None


# ============================================================================
# File Processing Functions
# ============================================================================

def get_file_hash(file_path):
    """Create a safe hash from file path for unique naming."""
    return str(file_path).replace("/", "_").replace(".", "_")


def process_file(kernel_path, build_path, file_path, is_original=True):
    """Process a single file: compile, disassemble, and manage artifacts."""
    rel_path = file_path.relative_to(kernel_path)
    obj_rel_path = rel_path.with_suffix(".o")
    obj_abs_path = kernel_path / obj_rel_path
    file_hash = get_file_hash(rel_path)
    
    dest_obj_file = build_path / f"{file_hash}.o"
    disas_file = build_path / f"{file_hash}_{'original' if is_original else 'recompiled'}.disas.txt"
    orig_obj_file = build_path / f"{file_hash}_{'original' if is_original else 'recompiled'}.orig.o"

    print_color(f"Compiling {rel_path}...", "blue")
    if not run_command(
        ["make", "KCFLAGS=-ffunction-sections -fdata-sections", str(obj_rel_path)],
        cwd=kernel_path
    ):
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
    """Search for files using the specified macro."""
    print_color(f"\nSearching for macro '{macro_name}' in kernel source...", "blue")
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

    files = set()
    for line in result.stdout.splitlines():
        file_path = line.split(":")[0]
        if file_path.endswith((".c", ".h")):
            files.add(Path(file_path))
    
    print_color(f"Found {len(files)} files using macro '{macro_name}':", "green")
    for file in sorted(files):
        print_color(f"   - {file.relative_to(kernel_path)}", "green")
    
    return sorted(files)


# ============================================================================
# Diff Analysis Functions
# ============================================================================

def strip_leading_number_colon(line):
    """Remove leading numbers followed by a colon (e.g., '3833:') from a line."""
    return re.sub(r'^\s*\d+:\s*', '', line)


def extract_instruction_bytes(line):
    """Extract instruction bytes from objdump line.
    
    For line like: "  e1:  66 41 39 c6             cmp    %ax,%r14w"
    Or diff line: "-  e1:  66 41 39 c6             cmp    %ax,%r14w"
    Returns: "66 41 39 c6" or None if not an instruction line.
    """
    # Match pattern: address:  bytes  mnemonic
    # Handle both normal lines and diff lines (with - or + prefix)
    match = re.match(r'^\s*[-+]?\s*[0-9a-fA-F]+:\s+([0-9a-fA-F\s]+)', line)
    if match:
        # Extract and normalize bytes (remove extra spaces)
        bytes_str = ' '.join(match.group(1).split())
        return bytes_str
    return None


def extract_mnemonic(line):
    """Extract mnemonic (instruction name) from objdump line.
    
    For line like: "  e1:  66 41 39 c6             cmp    %ax,%r14w"
    Returns: "cmp" or None if not an instruction line.
    """
    # Match pattern: address:  bytes  mnemonic operands
    # Extract mnemonic (word after bytes, before operands)
    # Handle both normal lines and diff lines (with - or + prefix)
    match = re.search(r'^\s*[-+]?\s*[0-9a-fA-F]+:\s+[0-9a-fA-F\s]+\s+([a-z]+)', line)
    if match:
        return match.group(1)
    return None


def extract_operand_types(line):
    """Extract operand type pattern from instruction line.
    
    For line like: "  e1:  66 41 39 c6             cmp    %ax,%r14w"
    Returns: ["reg", "reg"] - indicating two register operands.
    
    Operand types:
    - "imm": immediate value (e.g., $0xc8, $0xa)
    - "reg": register (e.g., %eax, %r8d, %rbx)
    - "mem": memory access (e.g., 0x4e8(%rbx), (%r12))
    - "label": label/symbol (e.g., function_name)
    """
    # Extract the operand part (after mnemonic)
    # Pattern: mnemonic operands (operands may contain spaces, commas, etc.)
    match = re.search(r'^\s*[-+]?\s*[0-9a-fA-F]+:\s+[0-9a-fA-F\s]+\s+[a-z]+\s+(.+)', line)
    if not match:
        return []
    
    operands_str = match.group(1).strip()
    if not operands_str:
        return []
    
    # Remove comments (everything after #)
    operands_str = operands_str.split('#')[0].strip()
    
    # Split by comma to get individual operands
    operands = [op.strip() for op in operands_str.split(',')]
    
    operand_types = []
    for op in operands:
        op = op.strip()
        if not op:
            continue
        
        # Check for immediate value (starts with $)
        if op.startswith('$'):
            operand_types.append('imm')
        # Check for memory access (contains ( or [)
        elif '(' in op or '[' in op:
            # For memory access, we want to preserve the offset if present
            # e.g., 0x4e8(%rbx) -> mem:0x4e8, (%rbx) -> mem:0
            mem_match = re.match(r'([0-9a-fA-Fx]+)?\s*\(', op)
            if mem_match:
                offset = mem_match.group(1) or '0'
                operand_types.append(f'mem:{offset}')
            else:
                operand_types.append('mem')
        # Check for label (contains < or >, or is a symbol name)
        elif '<' in op or '>' in op or (not op.startswith('%') and not any(c in op for c in '0123456789')):
            operand_types.append('label')
        # Otherwise, it's likely a register (starts with %)
        elif op.startswith('%'):
            operand_types.append('reg')
        else:
            # Default to reg for unknown patterns
            operand_types.append('reg')
    
    return operand_types


def normalize_instruction_for_comparison(line):
    """Normalize instruction for comparison, ignoring address offsets and register differences.
    
    For jump/call instructions, only compare opcode, not offset.
    For other instructions, compare mnemonic and operand type pattern (ignore register names).
    For continuation lines (no mnemonic), compare bytes only.
    Returns normalized instruction signature or None.
    """
    bytes_str = extract_instruction_bytes(line)
    if not bytes_str:
        return None
    
    mnemonic = extract_mnemonic(line)
    
    # If no mnemonic, this is likely a continuation line (e.g., "  fe:  00")
    # Compare bytes directly
    if not mnemonic:
        return f"bytes:{bytes_str}"
    
    # List of instructions that contain relative offsets/addresses
    offset_instructions = ['j', 'call', 'loop']
    
    # Check if this is a jump/call instruction
    is_offset_inst = any(mnemonic.startswith(prefix) for prefix in offset_instructions)
    
    if is_offset_inst:
        # For jump/call instructions, extract opcode (first 1-2 bytes typically)
        # and ignore the offset bytes (last 1-4 bytes)
        bytes_list = bytes_str.split()
        if len(bytes_list) >= 2:
            # Most jump/call instructions: opcode (1-2 bytes) + offset (1-4 bytes)
            # Try to identify opcode length based on first byte
            first_byte = bytes_list[0].lower()
            
            # Common patterns:
            # - 0x0f prefix: 2-byte opcode (e.g., 0f 87 = ja, 0f 85 = jne, 0f 84 = je)
            # - 0xe8, 0xe9: call/jmp with 1-byte opcode
            # - 0x70-0x7f: conditional jumps with 1-byte opcode
            try:
                if first_byte == '0f' and len(bytes_list) >= 3:
                    # Two-byte opcode (0f + opcode)
                    opcode = ' '.join(bytes_list[:2])
                elif first_byte in ['e8', 'e9', 'eb'] or (len(first_byte) == 2 and 
                                                           int(first_byte, 16) >= 0x70 and 
                                                           int(first_byte, 16) <= 0x7f):
                    # One-byte opcode
                    opcode = bytes_list[0]
                else:
                    # Fallback: use first 2 bytes as opcode
                    opcode = ' '.join(bytes_list[:min(2, len(bytes_list))])
            except (ValueError, IndexError):
                # If parsing fails, use first 2 bytes as fallback
                opcode = ' '.join(bytes_list[:min(2, len(bytes_list))])
            
            return f"{mnemonic}:{opcode}"
    else:
        # For non-jump instructions, compare mnemonic and operand type pattern
        # This allows us to ignore register differences (e.g., %eax vs %r8d)
        operand_types = extract_operand_types(line)
        operand_pattern = ','.join(operand_types) if operand_types else 'none'
        
        # Also extract immediate values for comparison (if any)
        # This helps distinguish instructions with different immediate values
        imm_values = []
        match = re.search(r'^\s*[-+]?\s*[0-9a-fA-F]+:\s+[0-9a-fA-F\s]+\s+[a-z]+\s+(.+)', line)
        if match:
            operands_str = match.group(1).split('#')[0].strip()
            # Extract immediate values (e.g., $0xc8, $0xa)
            imm_matches = re.findall(r'\$0x([0-9a-fA-F]+)', operands_str)
            imm_values = imm_matches
        
        # Build signature: mnemonic + operand pattern + immediate values
        if imm_values:
            return f"{mnemonic}:{operand_pattern}:imm={','.join(imm_values)}"
        else:
            return f"{mnemonic}:{operand_pattern}"


def filter_address_offset_diff(diff_lines):
    """Filter out differences that are only due to address offset.
    
    When instructions change length, all subsequent addresses shift.
    This function identifies and filters out lines where only the address
    changed but the instruction bytes are the same (or for jumps, only offset changed).
    
    Returns filtered diff lines.
    """
    filtered = []
    i = 0
    
    # First pass: collect all '-' and '+' lines with their signatures
    minus_lines = []
    plus_lines = []
    line_map = {}  # Map line index to whether it should be kept
    
    while i < len(diff_lines):
        line = diff_lines[i]
        
        # Keep non-instruction lines (headers, context, etc.)
        if not (line.startswith('-') or line.startswith('+')):
            line_map[i] = True
            i += 1
            continue
        
        if line.startswith('-'):
            # Pass the full line, function will handle the '-' prefix
            sig = normalize_instruction_for_comparison(line)
            if sig:
                minus_lines.append((i, sig, line))
            else:
                line_map[i] = True
        elif line.startswith('+'):
            # Pass the full line, function will handle the '+' prefix
            sig = normalize_instruction_for_comparison(line)
            if sig:
                plus_lines.append((i, sig, line))
            else:
                line_map[i] = True
        
        i += 1
    
    # Match minus and plus lines by signature
    matched_plus = set()
    
    for minus_idx, minus_sig, minus_line in minus_lines:
        # Find matching plus line with same signature
        matched = False
        for plus_idx, plus_sig, plus_line in plus_lines:
            if plus_idx not in matched_plus and minus_sig == plus_sig:
                # Found a match - mark both as filtered
                line_map[minus_idx] = False
                line_map[plus_idx] = False
                matched_plus.add(plus_idx)
                matched = True
                break
        
        if not matched:
            # No match found - keep the minus line
            line_map[minus_idx] = True
    
    # Mark unmatched plus lines as kept
    for plus_idx, _, _ in plus_lines:
        if plus_idx not in matched_plus:
            line_map[plus_idx] = True
    
    # Second pass: build filtered output and clean up isolated @@ lines
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]
        
        # Check if this is a @@ line
        if line.startswith('@@'):
            # Look ahead to see if there are any kept - or + lines in this hunk
            has_kept_changes = False
            j = i + 1
            while j < len(diff_lines) and not (diff_lines[j].startswith('@@') or 
                                                diff_lines[j].startswith('---') or
                                                diff_lines[j].startswith('+++')):
                if line_map.get(j, True) and (diff_lines[j].startswith('-') or 
                                              diff_lines[j].startswith('+')):
                    has_kept_changes = True
                    break
                j += 1
            
            # Only keep @@ line if there are kept changes in this hunk
            if has_kept_changes:
                filtered.append(line)
        else:
            # For other lines, use the line_map decision
            if line_map.get(i, True):
                filtered.append(line)
        
        i += 1
    
    return filtered


def diff_ignore_number_colon(file1, file2):
    """Diff two files, ignoring lines that only differ by leading numbers and colon."""
    with open(file1, "r") as f1, open(file2, "r") as f2:
        lines1 = [strip_leading_number_colon(l.rstrip('\n')) for l in f1]
        lines2 = [strip_leading_number_colon(l.rstrip('\n')) for l in f2]
    diff = list(difflib.unified_diff(
        lines1, lines2,
        fromfile=str(file1),
        tofile=str(file2),
        lineterm=''
    ))
    return diff


# ============================================================================
# Disassembly Analysis Functions
# ============================================================================

def parse_functions_from_disassembly(disas_file):
    """Parse disassembly file to extract function information.
    
    Returns a dict mapping function name to (start_addr, end_addr, size).
    Handles sections where each function has its own section.
    """
    functions = {}
    current_section = None
    section_functions = []
    section_last_addr = None
    
    with open(disas_file, "r") as f:
        for line in f:
            section_match = re.match(r'^Disassembly of section (\.text[^:]+):', line)
            if section_match:
                if section_functions:
                    for i, (start_addr, func_name) in enumerate(section_functions):
                        if i + 1 < len(section_functions):
                            end_addr = section_functions[i + 1][0]
                        else:
                            end_addr = section_last_addr if section_last_addr else start_addr
                        
                        start_int = int(start_addr, 16)
                        end_int = int(end_addr, 16)
                        size = end_int - start_int
                        functions[func_name] = (start_addr, end_addr, size)
                
                current_section = section_match.group(1)
                section_functions = []
                section_last_addr = None
                continue
            
            func_match = re.match(r'^([0-9a-fA-F]+)\s+<([^>]+)>:', line)
            if func_match:
                start_addr = func_match.group(1)
                func_name = func_match.group(2)
                if not func_name.startswith('__pfx_') and not func_name.endswith('.cold'):
                    section_functions.append((start_addr, func_name))
            
            if current_section:
                inst_match = re.match(r'^\s+([0-9a-fA-F]+):', line)
                if inst_match:
                    section_last_addr = inst_match.group(1)
    
    if section_functions:
        for i, (start_addr, func_name) in enumerate(section_functions):
            if i + 1 < len(section_functions):
                end_addr = section_functions[i + 1][0]
            else:
                end_addr = section_last_addr if section_last_addr else start_addr
            
            start_int = int(start_addr, 16)
            end_int = int(end_addr, 16)
            size = end_int - start_int
            functions[func_name] = (start_addr, end_addr, size)
    
    return functions


def find_function_for_address_in_file(disas_file, addr_str, line_number=None):
    """Find which function contains the given address by searching in the disassembly file.
    
    This is more accurate because it considers the section context.
    If line_number is provided, it will prioritize matches near that line number.
    Returns (function_name, start_addr, end_addr, size, instruction_count) or None.
    """
    try:
        addr = int(addr_str, 16)
    except ValueError:
        return None
    
    current_section = None
    current_func = None
    current_func_start = None
    best_match = None
    best_match_line = None
    
    with open(disas_file, "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        section_match = re.match(r'^Disassembly of section (\.text[^:]+):', line)
        if section_match:
            current_section = section_match.group(1)
            current_func = None
            current_func_start = None
            continue
        
        func_match = re.match(r'^([0-9a-fA-F]+)\s+<([^>]+)>:', line)
        if func_match:
            func_start = func_match.group(1)
            func_name = func_match.group(2)
            if not func_name.startswith('__pfx_') and not func_name.endswith('.cold'):
                current_func = func_name
                current_func_start = func_start
            continue
        
        if current_func and current_func_start:
            inst_match = re.match(r'^\s+([0-9a-fA-F]+):', line)
            if inst_match:
                inst_addr_str = inst_match.group(1)
                inst_addr = int(inst_addr_str, 16)
                
                if inst_addr == addr:
                    func_start_int = int(current_func_start, 16)
                    if func_start_int <= addr:
                        section_matches = True
                        if current_section:
                            section_func_name = current_section
                            if section_func_name.startswith('.text.unlikely.'):
                                section_func_name = section_func_name[len('.text.unlikely.'):]
                            elif section_func_name.startswith('.text.'):
                                section_func_name = section_func_name[len('.text.'):]
                            section_matches = (section_func_name == current_func)
                        
                        if section_matches:
                            func_end_int = inst_addr
                            func_start_line_idx = None
                            func_end_line_idx = i
                            
                            for j in range(i, -1, -1):
                                prev_line = lines[j]
                                prev_func_match = re.match(
                                    r'^([0-9a-fA-F]+)\s+<([^>]+)>:', prev_line
                                )
                                if (prev_func_match and
                                    prev_func_match.group(1) == current_func_start):
                                    func_start_line_idx = j
                                    break
                            
                            for j in range(i + 1, len(lines)):
                                next_line = lines[j]
                                next_func_match = re.match(
                                    r'^([0-9a-fA-F]+)\s+<([^>]+)>:', next_line
                                )
                                next_section_match = re.match(
                                    r'^Disassembly of section', next_line
                                )
                                if next_func_match or next_section_match:
                                    break
                                
                                next_inst_match = re.match(r'^\s+([0-9a-fA-F]+):', next_line)
                                if next_inst_match:
                                    func_end_int = int(next_inst_match.group(1), 16)
                                    func_end_line_idx = j
                            
                            instruction_count = 0
                            if func_start_line_idx is not None:
                                for j in range(func_start_line_idx + 1, func_end_line_idx + 1):
                                    inst_match = re.match(r'^\s+([0-9a-fA-F]+):', lines[j])
                                    if inst_match:
                                        instruction_count += 1
                            
                            size = func_end_int - func_start_int
                            if line_number is not None:
                                distance = abs(i + 1 - line_number)
                                if (best_match is None or
                                    (best_match_line is not None and
                                     distance < abs(best_match_line - line_number))):
                                    best_match = (
                                        current_func, current_func_start,
                                        f"{func_end_int:x}", size, instruction_count
                                    )
                                    best_match_line = i + 1
                            else:
                                best_match = (
                                    current_func, current_func_start,
                                    f"{func_end_int:x}", size, instruction_count
                                )
                                best_match_line = i + 1
    
    return best_match


def find_function_for_address(functions, addr_str, disas_file, line_number=None):
    """Find which function contains the given address.
    
    Uses section-aware search for accurate function matching.
    If line_number is provided, it will prioritize matches near that line number.
    Returns (function_name, start_addr, end_addr, size, instruction_count) or None.
    """
    if disas_file:
        return find_function_for_address_in_file(disas_file, addr_str, line_number)
    return None


def parse_instructions_from_disassembly(disas_file):
    """Parse disassembly file to extract all instructions with their addresses.
    
    Returns a list of (address, instruction_line, line_number) tuples, sorted by address.
    """
    instructions = []
    labels = set()  # Set of addresses that are labels (function starts)
    
    with open(disas_file, "r") as f:
        lines = f.readlines()
    
    # First pass: identify function labels
    for line in lines:
        func_match = re.match(r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:', line)
        if func_match:
            addr = func_match.group(1)
            labels.add(addr)
    
    # Second pass: extract instructions
    for line_num, line in enumerate(lines, 1):
        # Match section header (skip)
        section_match = re.match(r'^Disassembly of section', line)
        if section_match:
            continue
        
        # Match function definition (skip, already handled)
        func_match = re.match(r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:', line)
        if func_match:
            continue
        
        # Match instruction line: "  address:  bytes  mnemonic operands"
        inst_match = re.match(r'^\s+([0-9a-fA-F]+):\s+(.+)', line)
        if inst_match:
            addr = inst_match.group(1)
            inst_line = inst_match.group(2).strip()
            is_label = addr in labels
            instructions.append((addr, inst_line, is_label, line_num))
    
    return instructions


def is_basic_block_terminator(mnemonic):
    """Check if an instruction is a basic block terminator.
    
    Basic block terminators include:
    - Unconditional jumps (jmp)
    - Conditional jumps (je, jne, ja, etc.)
    - Calls (call)
    - Returns (ret, retq)
    """
    if not mnemonic:
        return False
    
    # Unconditional jumps
    if mnemonic == 'jmp':
        return True
    
    # Conditional jumps (all start with 'j' except jmp)
    if mnemonic.startswith('j') and mnemonic != 'jmp':
        return True
    
    # Calls
    if mnemonic == 'call':
        return True
    
    # Returns
    if mnemonic in ['ret', 'retq', 'retn']:
        return True
    
    return False


def find_instruction_line_in_file(disas_file, addr_str, function_name=None):
    """Find the line number in disassembly file for a given address.
    
    Returns (line_number, instruction_line) or (None, None) if not found.
    """
    try:
        target_addr = int(addr_str, 16)
    except ValueError:
        return None, None
    
    instructions = parse_instructions_from_disassembly(disas_file)
    if not instructions:
        return None, None
    
    # If function_name is provided, find the function first
    if function_name:
        # Find function start
        func_start_idx = None
        for i, (addr, inst_line, is_label, line_num) in enumerate(instructions):
            if is_label:
                # Check if this is the target function
                with open(disas_file, "r") as f:
                    lines = f.readlines()
                    if line_num <= len(lines):
                        func_match = re.match(
                            r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:',
                            lines[line_num - 1]
                        )
                        if func_match and func_match.group(2) == function_name:
                            func_start_idx = i
                            break
        
        if func_start_idx is None:
            return None, None
        
        # Find function end (next label or end of instructions)
        func_end_idx = len(instructions)
        for i in range(func_start_idx + 1, len(instructions)):
            addr, inst_line, is_label, line_num = instructions[i]
            if is_label:
                func_end_idx = i
                break
        
        # Search only within this function
        func_instructions = instructions[func_start_idx:func_end_idx]
    else:
        func_instructions = instructions
    
    # Find the instruction at the target address
    for addr, inst_line, is_label, line_num in func_instructions:
        try:
            inst_addr = int(addr, 16)
            if inst_addr == target_addr:
                return line_num, inst_line
            elif inst_addr > target_addr:
                # Address not found
                return None, None
        except ValueError:
            continue
    
    return None, None


def find_basic_block_for_address(disas_file, addr_str, function_name=None):
    """Find the basic block containing the given address.
    
    If function_name is provided, searches only within that function.
    Otherwise, searches all functions (addresses are relative to function start).
    
    Returns a list of (address, instruction_line) tuples representing the basic block,
    or None if the address is not found.
    """
    try:
        target_addr = int(addr_str, 16)
    except ValueError:
        return None
    
    instructions = parse_instructions_from_disassembly(disas_file)
    if not instructions:
        return None
    
    # If function_name is provided, find the function first
    if function_name:
        # Find function start
        func_start_idx = None
        for i, (addr, inst_line, is_label, line_num) in enumerate(instructions):
            if is_label:
                # Check if this is the target function
                # We need to check the original file for function name
                with open(disas_file, "r") as f:
                    lines = f.readlines()
                    if line_num <= len(lines):
                        func_match = re.match(
                            r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:',
                            lines[line_num - 1]
                        )
                        if func_match and func_match.group(2) == function_name:
                            func_start_idx = i
                            break
        
        if func_start_idx is None:
            return None
        
        # Find function end (next label or end of instructions)
        func_end_idx = len(instructions)
        for i in range(func_start_idx + 1, len(instructions)):
            addr, inst_line, is_label, line_num = instructions[i]
            if is_label:
                func_end_idx = i
                break
        
        # Search only within this function
        func_instructions = instructions[func_start_idx:func_end_idx]
    else:
        func_instructions = instructions
    
    # Find the instruction at the target address within the function
    target_idx = None
    for i, (addr, inst_line, is_label, line_num) in enumerate(func_instructions):
        try:
            inst_addr = int(addr, 16)
            if inst_addr == target_addr:
                target_idx = i
                break
            elif inst_addr > target_addr:
                # Address not found in this function
                return None
        except ValueError:
            continue
    
    if target_idx is None:
        return None
    
    # Use function instructions for searching, but track absolute indices
    if function_name:
        # Search within function, but need to map back to absolute indices
        func_target_idx = target_idx
        search_start = func_start_idx
        search_end = func_end_idx
    else:
        func_target_idx = target_idx
        search_start = 0
        search_end = len(func_instructions)
    
    # Find basic block start (go backwards until we find a label or terminator)
    start_idx = func_target_idx
    for i in range(func_target_idx, -1, -1):
        addr, inst_line, is_label, line_num = func_instructions[i]
        
        # If this is a label (function start), it's a basic block start
        if is_label:
            start_idx = i
            break
        
        # Extract mnemonic
        mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
        
        # Check if this is a basic block terminator
        if is_basic_block_terminator(mnemonic):
            # This instruction ends a basic block, start from next one
            if i + 1 < len(func_instructions):
                start_idx = i + 1
            else:
                return None
            break
        
        start_idx = i
    
    # Find basic block end (go forwards until we find a terminator or label)
    end_idx = start_idx
    for i in range(start_idx, len(func_instructions)):
        addr, inst_line, is_label, line_num = func_instructions[i]
        
        # If this is a label and it's not the start, it's a new basic block
        if is_label and i > start_idx:
            end_idx = i - 1
            break
        
        # Extract mnemonic
        mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
        
        # Check if this is a basic block terminator
        if is_basic_block_terminator(mnemonic):
            end_idx = i
            break
        
        end_idx = i
    
    # Extract the basic block
    basic_block = []
    for i in range(start_idx, end_idx + 1):
        addr, inst_line, is_label, line_num = func_instructions[i]
        basic_block.append((addr, inst_line))
    
    return basic_block if basic_block else None


def get_basic_block_key(basic_block):
    """Generate a unique key for a basic block to identify duplicates.
    
    Uses the first and last addresses as the key.
    """
    if not basic_block:
        return None
    return (basic_block[0][0], basic_block[-1][0])


# ============================================================================
# File Modification Functions
# ============================================================================

def macro_to_pattern(line):
    """Convert macro definition line to regex pattern."""
    m = re.match(r"^#define\s+(\w+)\s+(.+)$", line)
    if m:
        macro, value = m.group(1), m.group(2)
        pattern = rf"#define\s+{re.escape(macro)}\s+{re.escape(value.strip())}"
        pattern = pattern.replace(r"\s+", r"[ \t]+")
        return pattern
    return re.escape(line)


def modify_file_with_sed(source_file, from_code, to_code):
    """Modify file using sed and return restore expression."""
    from_pattern = macro_to_pattern(from_code)
    to_code_stripped = to_code.strip()
    from_code_stripped = from_code.strip()
    sed_expr = f"s|{from_pattern}|{to_code_stripped}|g"
    
    if not run_command(["sed", "-i", "-E", sed_expr, str(source_file)], cwd=source_file.parent):
        raise RuntimeError("Failed to modify file using sed.")
    
    sed_expr_for_restoring = f"s|{to_code_stripped}|{from_code_stripped}|g"
    return sed_expr_for_restoring, to_code_stripped, from_code_stripped


def restore_file_from_backup(source_file, backup_file, sed_expr_for_restoring,
                              to_code_stripped, from_code_stripped):
    """Restore original file from backup or using sed."""
    if backup_file.exists():
        shutil.copy2(str(backup_file), str(source_file))
        print_color("   Original file restored from backup successfully.", "green")
        backup_file.unlink()
        print_color("   Backup file cleaned up.", "green")
    else:
        print_color(
            f"   Backup not found, using sed restore pattern: {sed_expr_for_restoring}",
            "yellow"
        )
        if not run_command(
            ["sed", "-i", "-E", sed_expr_for_restoring, str(source_file)],
            cwd=source_file.parent
        ):
            print_color(
                "   Warning: sed restore failed, trying alternative method...",
                "yellow"
            )
            if "|" in to_code_stripped or "|" in from_code_stripped:
                alt_sed_expr = f"s#{to_code_stripped}#{from_code_stripped}#g"
                print_color(f"   Trying alternative pattern: {alt_sed_expr}", "yellow")
                if not run_command(
                    ["sed", "-i", "-E", alt_sed_expr, str(source_file)],
                    cwd=source_file.parent
                ):
                    raise RuntimeError(
                        "Failed to restore the original file with alternative method."
                    )
            else:
                raise RuntimeError("Failed to restore the original file.")
        print_color("   Original file restored successfully via sed.", "green")


# ============================================================================
# Main Function
# ============================================================================

def parse_lines_argument(lines_str):
    """Parse lines argument to support formats like xxx-xxx,xxx,xxx-xxx,xxx."""
    line_set = set()
    for part in lines_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-")
                start, end = int(start), int(end)
                if start > end:
                    start, end = end, start
                line_set.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                line_set.add(int(part))
            except ValueError:
                continue
    return sorted(line_set)


def process_addr2line(obj_file, offset, line, lines_filter, changed_instructions,
                       current_diff_line_number):
    """Process addr2line for a single offset."""
    addr2line_cmd = ["addr2line", "-e", str(obj_file), offset]
    result = subprocess.run(addr2line_cmd, capture_output=True, text=True)
    
    if result.stdout:
        if lines_filter:
            line_number_str = result.stdout.split(":")[1].split(" ")[0].rstrip("\n")
            try:
                line_number = int(line_number_str)
                if line_number in lines_filter:
                    print(line + "\t" + result.stdout, end="")
                    changed_instructions.append((line, offset, current_diff_line_number))
            except ValueError:
                pass
        else:
            print(line + "\t" + result.stdout, end="")
            changed_instructions.append((line, offset, current_diff_line_number))
    
    return changed_instructions


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
        required=True,
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
    parser.add_argument(
        "--vmlinux", "-V",
        action="store_true",
        help="Diff vmlinux instead of individual .o files. More accurate for cross-file inlining."
    )
    parser.add_argument(
        "--func", "-F",
        nargs="*",
        help="Function names to analyze in vmlinux mode. Auto-detected if not specified."
    )
    args = parser.parse_args()
    
    kernel_path = Path(args.path).resolve()
    
    if args.lines:
        args.lines = parse_lines_argument(args.lines)
    
    # Environment check
    check_tools()
    source_file = kernel_path / args.file
    build_path = kernel_path / BUILD_DIR_NAME

    print_color("2. Checking paths and files...", "blue")
    if not kernel_path.is_dir():
        print_color(
            f"Error: Kernel source path '{kernel_path}' does not exist or is not a directory.",
            "red"
        )
        sys.exit(1)
    
    if not source_file.is_file():
        print_color(f"Error: Source file '{source_file}' does not exist.", "red")
        sys.exit(1)
    
    build_path.mkdir(exist_ok=True)
    
    print_color(f"   - Kernel Path: {kernel_path}", "green")
    print_color(f"   - Target File: {source_file}", "green")
    print_color(f"   - Output Dir: {build_path}\n", "green")

    original_disas = {}
    recompiled_disas = {}
    diff_result = None

    try:
        # Vmlinux mode: Two-phase approach
        if args.vmlinux:
            if not args.sed:
                print_color("Error: --vmlinux mode requires --sed to specify the modification.", "red")
                sys.exit(1)

            from_code, to_code = args.sed
            affected_functions = set()

            # Phase 1: Quick .o diff to detect affected functions (if --func not specified)
            if not args.func:
                print_color("=== Phase 1: Quick .o diff to detect affected functions ===", "blue")

                # Compile original .o
                print_color("3. Performing initial compilation for target file...", "blue")
                target_obj, target_orig_disas, target_orig_obj = process_file(
                    kernel_path, build_path, source_file, is_original=True
                )
                original_disas[source_file] = target_orig_disas

                # Modify file
                print_color("\n4. Modifying file using sed...", "blue")
                backup_file = build_path / f"{source_file.name}.backup"
                shutil.copy2(str(source_file), str(backup_file))
                print_color(f"   Created backup: {backup_file}", "green")

                sed_expr_for_restoring, to_code_stripped, from_code_stripped = (
                    modify_file_with_sed(source_file, from_code, to_code)
                )
                print_color("   File modified successfully.\n", "yellow")

                # Compile modified .o
                print_color("5. Recompiling modified target file...", "blue")
                _, target_recomp_disas, target_recomp_obj = process_file(
                    kernel_path, build_path, source_file, is_original=False
                )
                recompiled_disas[source_file] = target_recomp_disas

                # Diff to find affected functions
                print_color("\n6. Comparing .o disassembly to detect affected functions...", "blue")
                diff_cmd = [
                    "diff", str(original_disas[source_file]),
                    str(recompiled_disas[source_file]), "-U0"
                ]
                diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)

                if diff_result.stdout:
                    diff_lines = diff_result.stdout.splitlines()
                    filtered_diff = filter_address_offset_diff(diff_lines)
                    if filtered_diff:
                        class FilteredDiffResult:
                            def __init__(self, diff_lines):
                                self.stdout = '\n'.join(diff_lines)
                        diff_result = FilteredDiffResult(filtered_diff)
                        affected_functions = detect_affected_functions_from_diff(
                            diff_result, original_disas[source_file]
                        )
                        print_color(f"   Auto-detected affected functions: {affected_functions}", "green")
                    else:
                        print_color("   No real differences found in .o file", "yellow")
                else:
                    print_color("   No differences found in .o file", "yellow")

                # Restore original file
                print_color("\n7. Restoring the original file...", "blue")
                restore_file_from_backup(
                    source_file, backup_file, sed_expr_for_restoring,
                    to_code_stripped, from_code_stripped
                )
                print_color("   Original file restored successfully.\n", "green")
            else:
                affected_functions = set(args.func)
                print_color(f"Using user-specified functions: {affected_functions}", "blue")

            if not affected_functions:
                print_color("No affected functions detected. Nothing to do in vmlinux mode.", "yellow")
                sys.exit(0)

            # Phase 2: Full vmlinux diff for precise binary
            print_color("\n=== Phase 2: Building and diffing vmlinux for precise analysis ===", "blue")

            # Build original vmlinux
            print_color("\n8. Building original vmlinux...", "blue")
            original_vmlinux = build_vmlinux(kernel_path, build_path, is_original=True)

            # Disassemble affected functions from original vmlinux
            original_func_disas = {}
            for func in affected_functions:
                print_color(f"\n   Disassembling function {func} from original vmlinux...", "blue")
                original_func_disas[func] = disassemble_function_from_vmlinux(
                    original_vmlinux, build_path, func, "original"
                )

            # Modify source and rebuild vmlinux
            print_color("\n9. Modifying source file for vmlinux rebuild...", "blue")
            backup_file = build_path / f"{source_file.name}.backup.vmlinux"
            shutil.copy2(str(source_file), str(backup_file))
            print_color(f"   Created backup: {backup_file}", "green")

            sed_expr_for_restoring, to_code_stripped, from_code_stripped = (
                modify_file_with_sed(source_file, from_code, to_code)
            )
            print_color("   File modified successfully.\n", "yellow")

            # Build recompiled vmlinux
            print_color("\n10. Building recompiled vmlinux...", "blue")
            recompiled_vmlinux = build_vmlinux(kernel_path, build_path, is_original=False)

            # Disassemble affected functions from recompiled vmlinux
            recompiled_func_disas = {}
            for func in affected_functions:
                print_color(f"\n   Disassembling function {func} from recompiled vmlinux...", "blue")
                recompiled_func_disas[func] = disassemble_function_from_vmlinux(
                    recompiled_vmlinux, build_path, func, "recompiled"
                )

            # Restore original file
            print_color("\n11. Restoring the original file...", "blue")
            restore_file_from_backup(
                source_file, backup_file, sed_expr_for_restoring,
                to_code_stripped, from_code_stripped
            )
            print_color("   Original file restored successfully.\n", "green")

            # Diff each function
            print_color("\n12. Comparing vmlinux function disassemblies...", "blue")
            for func in affected_functions:
                print_color(f"\n--- Diff for function {func} (vmlinux) ---", "yellow")

                if func not in original_func_disas or func not in recompiled_func_disas:
                    print_color(f"   Skipping {func}: disassembly not available", "yellow")
                    continue

                diff_cmd = [
                    "diff", str(original_func_disas[func]),
                    str(recompiled_func_disas[func]), "-U0"
                ]
                func_diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)

                if func_diff_result.stdout:
                    diff_lines = func_diff_result.stdout.splitlines()
                    filtered_diff = filter_address_offset_diff(diff_lines)
                    if filtered_diff:
                        print_color("\nFiltered diff (address offset differences removed):", "blue")
                        for line in filtered_diff:
                            print(line)

                        # Parse diff with proper offset calculation
                        print_color(f"\nChanged instructions in {func} (with offsets from vmlinux):", "blue")
                        changed_instrs = parse_vmlinux_diff_with_offsets(
                            filtered_diff, original_func_disas[func], func
                        )

                        for offset, line, is_original in changed_instrs:
                            prefix = "Original" if is_original else "Modified"
                            print(f"  [{prefix}] offset {offset}: {line}")

                        # Show kprobe attachment info for original instructions
                        print_color(f"\nKprobe attachment info for {func}:", "blue")
                        for offset, line, is_original in changed_instrs:
                            if is_original:
                                changed_offset = int(offset, 16)
                                kprobe_offset = find_next_instruction_offset(
                                    original_func_disas[func], func, changed_offset
                                )
                                if kprobe_offset is not None:
                                    print(f"  Changed instruction at offset: {offset}")
                                    print(f"  Kprobe attach point (next instr): 0x{kprobe_offset:x}")
                                    print(f"  SEC(\"kprobe/{func}+0x{kprobe_offset:x}\")")
                    else:
                        print_color("No real differences found (only address offsets changed)", "green")
                else:
                    print_color("No differences found", "green")

            print_color("\nVmlinux analysis complete.", "blue")
            print_color(f"Vmlinux files saved to: {build_path}", "green")
            print_color(f"  - Original: vmlinux_original", "green")
            print_color(f"  - Recompiled: vmlinux_recompiled", "green")
            for func in affected_functions:
                print_color(f"  - {func} disassembly: vmlinux_{func}_*.disas.txt", "green")

            sys.exit(0)

        # Normal .o file mode (original behavior)
        # Initial compilation for target file
        print_color("3. Performing initial compilation for target file...", "blue")
        target_obj, target_orig_disas, target_orig_obj = process_file(
            kernel_path, build_path, source_file, is_original=True
        )
        original_disas[source_file] = target_orig_disas

        # Find macro-using files (if specified)
        macro_files = []
        if args.macro:
            macro_files = search_macro_usage(kernel_path, args.macro)
            for file in macro_files:
                if file != source_file:
                    obj, disas, orig_obj = process_file(
                        kernel_path, build_path, file, is_original=True
                    )
                    original_disas[file] = disas

        # Modify file (if --sed is provided)
        if args.sed:
            print_color("\n5. Modifying file using sed...", "blue")
            from_code, to_code = args.sed
            
            backup_file = build_path / f"{source_file.name}.backup"
            shutil.copy2(str(source_file), str(backup_file))
            print_color(f"   Created backup: {backup_file}", "green")
            
            sed_expr_for_restoring, to_code_stripped, from_code_stripped = (
                modify_file_with_sed(source_file, from_code, to_code)
            )
            print_color("   File modified successfully.\n", "yellow")

            # Recompilation for target file
            print_color("6. Recompiling modified target file...", "blue")
            _, target_recomp_disas, target_recomp_obj = process_file(
                kernel_path, build_path, source_file, is_original=False
            )
            recompiled_disas[source_file] = target_recomp_disas

            # Recompile macro-using files
            if args.macro and macro_files:
                print_color("\n7. Recompiling files using specified macro...", "blue")
                for file in macro_files:
                    _, disas, orig_obj = process_file(
                        kernel_path, build_path, file, is_original=False
                    )
                    recompiled_disas[file] = disas

            # Diff comparison
            print_color("\n8. Comparing disassembly results...", "blue")
            for file in original_disas:
                if file in recompiled_disas:
                    print_color(
                        f"\n--- Diff for {file.relative_to(kernel_path)} ---",
                        "yellow"
                    )
                    if args.ignore_number_colon:
                        diff = diff_ignore_number_colon(
                            original_disas[file], recompiled_disas[file]
                        )
                        if diff:
                            # Filter out address offset differences
                            filtered_diff = filter_address_offset_diff(diff)
                            if filtered_diff:
                                print_color(
                                    "\nFiltered diff (address offset differences removed):",
                                    "blue"
                                )
                                for line in filtered_diff:
                                    print(line)
                                class MockDiffResult:
                                    def __init__(self, diff_lines):
                                        self.stdout = '\n'.join(diff_lines)
                                diff_result = MockDiffResult(filtered_diff)
                            else:
                                print_color(
                                    "No real differences found (only address offsets changed)",
                                    "green"
                                )
                                diff_result = None
                        else:
                            print_color("No differences found", "green")
                            diff_result = None
                    else:
                        diff_cmd = [
                            "diff", str(original_disas[file]),
                            str(recompiled_disas[file]), "-U0"
                        ]
                        diff_result = subprocess.run(
                            diff_cmd, capture_output=True, text=True
                        )
                        if diff_result.stdout:
                            # Filter out address offset differences
                            diff_lines = diff_result.stdout.splitlines()
                            filtered_diff = filter_address_offset_diff(diff_lines)
                            if filtered_diff:
                                print_color(
                                    "\nFiltered diff (address offset differences removed):",
                                    "blue"
                                )
                                print('\n'.join(filtered_diff))
                                # Update diff_result with filtered output
                                class FilteredDiffResult:
                                    def __init__(self, diff_lines):
                                        self.stdout = '\n'.join(diff_lines)
                                diff_result = FilteredDiffResult(filtered_diff)
                            else:
                                print_color(
                                    "No real differences found (only address offsets changed)",
                                    "green"
                                )
                                diff_result = None
                        else:
                            print_color("No differences found", "green")
                            diff_result = None
            
            # Restore original file
            print_color("\n9. Restoring the original file...", "blue")
            restore_file_from_backup(
                source_file, backup_file, sed_expr_for_restoring,
                to_code_stripped, from_code_stripped
            )
            print_color("   Original file restored successfully.\n", "green")
        else:
            print_color(
                "Skipping modification, recompilation, and diff steps because --sed was not provided.",
                "yellow"
            )

        # Use addr2line to get source-code lines for changed instructions
        if args.sed and diff_result and diff_result.stdout:
            print_color(
                "\n10. Using addr2line to get all source-code lines for the instructions that have changed...",
                "blue"
            )
            changed_instructions = []
            changed_instructions_recompiled = []  # For recompiled file instructions
            current_diff_line_number = None
            current_hunk_start = None  # Starting line number in original file for current hunk
            current_hunk_line_offset = 0  # Offset within current hunk (only counting - and context lines)
            current_hunk_start_recompiled = None  # Starting line number in recompiled file for current hunk
            current_hunk_line_offset_recompiled = 0  # Offset within current hunk for recompiled file
            
            for line in diff_result.stdout.splitlines():
                if line.startswith("@@"):
                    # Parse @@ -old_start,old_count +new_start,new_count @@
                    match = re.search(r'@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@', line)
                    if match:
                        current_hunk_start = int(match.group(1))
                        current_hunk_line_offset = 0
                        current_diff_line_number = current_hunk_start
                        current_hunk_start_recompiled = int(match.group(3))
                        current_hunk_line_offset_recompiled = 0
                
                # Track line numbers: - lines are from original file, + lines are from new file
                # Context lines (starting with space) are in both files
                original_line_num = None
                recompiled_line_num = None
                
                if line.startswith(' ') or line.startswith('-'):
                    # This line exists in original file
                    if current_hunk_start is not None:
                        original_line_num = current_hunk_start + current_hunk_line_offset
                        current_hunk_line_offset += 1
                    # Context lines also exist in recompiled file
                    if line.startswith(' ') and current_hunk_start_recompiled is not None:
                        recompiled_line_num = current_hunk_start_recompiled + current_hunk_line_offset_recompiled
                        current_hunk_line_offset_recompiled += 1
                elif line.startswith('+'):
                    # This line only exists in recompiled file
                    if current_hunk_start_recompiled is not None:
                        recompiled_line_num = current_hunk_start_recompiled + current_hunk_line_offset_recompiled
                        current_hunk_line_offset_recompiled += 1
                
                # Process original file instructions (- lines)
                flag = "+" if args.reverse else "-"
                if line.startswith(flag):
                    if len(line.split()) < 2:
                        continue
                    
                    offset = line.split()[1].rstrip(':')
                    obj = target_recomp_obj if args.reverse else target_orig_obj
                    # Store original file line number along with instruction info
                    changed_instructions = process_addr2line(
                        obj, offset, line, args.lines, changed_instructions,
                        original_line_num  # Pass the actual line number in original file
                    )
                
                # Process recompiled file instructions (+ lines)
                flag_recompiled = "-" if args.reverse else "+"
                if line.startswith(flag_recompiled):
                    if len(line.split()) < 2:
                        continue
                    
                    offset = line.split()[1].rstrip(':')
                    obj = target_orig_obj if args.reverse else target_recomp_obj
                    # Store recompiled file line number along with instruction info
                    changed_instructions_recompiled = process_addr2line(
                        obj, offset, line, args.lines, changed_instructions_recompiled,
                        recompiled_line_num  # Pass the actual line number in recompiled file
                    )
            
            # Extract Basic Blocks for changed instructions from step 10
            if changed_instructions:
                print_color(
                    "\n11. Extracting Basic Blocks for changed instructions...",
                    "blue"
                )
                original_disas_file = original_disas[source_file]
                seen_blocks = {}  # Map (start_addr, end_addr) -> basic_block
                seen_line_ranges = []  # List of (start_line, end_line) tuples for already output Basic Blocks
                
                # Collect all changed instruction addresses for marking
                changed_addresses_int = set()  # Store as integers for reliable comparison
                changed_line_numbers = set()
                
                # Read the original disassembly file to get line-by-line access
                with open(original_disas_file, "r") as f:
                    original_lines = f.readlines()
                
                # First pass: collect all changed addresses and line numbers
                for line, offset, original_line_num in changed_instructions:
                    # Skip diff header lines (---, +++, @@, etc.)
                    if (line.startswith('---') or line.startswith('+++') or 
                        line.startswith('@@') or not line.strip()):
                        continue
                    
                    # Extract address from the line
                    addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
                    if addr_match:
                        addr_str = addr_match.group(1)
                        try:
                            addr_int = int(addr_str, 16)
                            changed_addresses_int.add(addr_int)
                            if original_line_num:
                                changed_line_numbers.add(original_line_num)
                        except ValueError:
                            pass
                
                # Second pass: extract Basic Blocks
                for line, offset, original_line_num in changed_instructions:
                    # Skip diff header lines (---, +++, @@, etc.)
                    if (line.startswith('---') or line.startswith('+++') or 
                        line.startswith('@@') or not line.strip()):
                        continue
                    
                    # Extract address from the line (format: "-   3:  be c8 00 00 00")
                    addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
                    if not addr_match:
                        continue
                    
                    addr_str = addr_match.group(1)
                    
                    # Use the line number from step 8's diff output
                    if original_line_num is None or original_line_num < 1 or original_line_num > len(original_lines):
                        print_color(
                            f"Invalid line number {original_line_num} for address 0x{addr_str}",
                            "yellow"
                        )
                        continue
                    
                    # Check if this line is already covered by a previously output Basic Block
                    already_covered = False
                    for start_line, end_line in seen_line_ranges:
                        if start_line <= original_line_num <= end_line:
                            already_covered = True
                            break
                    
                    if already_covered:
                        # Skip this instruction as it's already in a Basic Block we've output
                        continue
                    
                    # Step 1: Get the instruction line from original file using line number from diff
                    inst_line_content = original_lines[original_line_num - 1].strip()
                    
                    # Step 2: Find basic block starting from this specific line number
                    # Parse all instructions with their line numbers
                    instructions = parse_instructions_from_disassembly(original_disas_file)
                    
                    # Find the instruction at the target line number
                    target_inst_idx = None
                    for i, (addr, inst_line, is_label, line_num) in enumerate(instructions):
                        if line_num == original_line_num:
                            target_inst_idx = i
                            break
                    
                    if target_inst_idx is None:
                        print_color(
                            f"Could not find instruction at line {original_line_num}",
                            "yellow"
                        )
                        continue
                    
                    # Find basic block boundaries starting from this instruction
                    # Go backwards to find basic block start
                    start_idx = target_inst_idx
                    for i in range(target_inst_idx, -1, -1):
                        addr, inst_line, is_label, line_num = instructions[i]
                        
                        # If this is a label (function start), it's a basic block start
                        if is_label:
                            start_idx = i
                            break
                        
                        # Extract mnemonic
                        mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
                        
                        # Check if this is a basic block terminator
                        if is_basic_block_terminator(mnemonic):
                            # This instruction ends a basic block, start from next one
                            if i + 1 < len(instructions):
                                start_idx = i + 1
                            else:
                                start_idx = target_inst_idx
                            break
                        
                        start_idx = i
                    
                    # Go forwards to find basic block end
                    end_idx = start_idx
                    for i in range(start_idx, len(instructions)):
                        addr, inst_line, is_label, line_num = instructions[i]
                        
                        # If this is a label and it's not the start, it's a new basic block
                        if is_label and i > start_idx:
                            end_idx = i - 1
                            break
                        
                        # Extract mnemonic
                        mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
                        
                        # Check if this is a basic block terminator
                        if is_basic_block_terminator(mnemonic):
                            end_idx = i
                            break
                        
                        end_idx = i
                    
                    # Extract the basic block
                    basic_block = []
                    bb_start_line = None
                    bb_end_line = None
                    for i in range(start_idx, end_idx + 1):
                        addr, inst_line, is_label, line_num = instructions[i]
                        basic_block.append((addr, inst_line))
                        if bb_start_line is None:
                            bb_start_line = line_num
                        bb_end_line = line_num
                    
                    if basic_block:
                        block_key = get_basic_block_key(basic_block)
                        if block_key and block_key not in seen_blocks:
                            seen_blocks[block_key] = basic_block
                            # Record the line number range for this Basic Block
                            if bb_start_line and bb_end_line:
                                seen_line_ranges.append((bb_start_line, bb_end_line))
                            
                            # Find the function name for this Basic Block
                            # Look backwards from bb_start_line in the file to find function definition
                            function_name = None
                            section_name = None
                            
                            # Search backwards from bb_start_line to find function definition
                            for line_idx in range(bb_start_line - 1, -1, -1):
                                if line_idx >= len(original_lines):
                                    break
                                line_content = original_lines[line_idx]
                                
                                # Check for function definition: "  address: <function_name>:"
                                func_match = re.match(
                                    r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:',
                                    line_content
                                )
                                if func_match:
                                    func_addr = func_match.group(1)
                                    func_name = func_match.group(2)
                                    # Skip prefix functions
                                    # if not func_name.startswith('__pfx_') and not func_name.endswith('.cold'):
                                    function_name = func_name
                                    
                                    # Also try to find section name
                                    # Look backwards for section header
                                    for j in range(line_idx - 1, -1, -1):
                                        if j < len(original_lines):
                                            section_line = original_lines[j]
                                            section_match = re.match(
                                                r'^Disassembly of section (\.text[^:]+):',
                                                section_line
                                            )
                                            if section_match:
                                                section_name = section_match.group(1)
                                                break
                                    break
                                
                                # Stop if we hit a section header (went too far back)
                                if re.match(r'^Disassembly of section', line_content):
                                    break
                            
                            print_color(
                                f"Basic Block: lines {bb_start_line}-{bb_end_line}",
                                "yellow"
                            )
                            if function_name:
                                print(f"Function: {function_name}")
                            else:
                                print(f"Function: Not found")
                            
                            for addr, inst_line in basic_block:
                                # Mark changed instructions with [*]
                                # Convert address to integer for comparison
                                try:
                                    addr_int = int(addr, 16)
                                    if addr_int in changed_addresses_int:
                                        print(f"  [*] {addr}:  {inst_line}")
                                    else:
                                        print(f"  {addr}:  {inst_line}")
                                except ValueError:
                                    # If address parsing fails, output without mark
                                    print(f"  {addr}:  {inst_line}")
                    else:
                        print_color(
                            f"Could not find Basic Block for line {original_line_num}",
                            "yellow"
                        )
                
                # Extract Basic Blocks for recompiled file instructions
                if changed_instructions_recompiled:
                    print_color(
                        "\n11b. Extracting Basic Blocks for changed instructions (recompiled)...",
                        "blue"
                    )
                    recompiled_disas_file = recompiled_disas[source_file]
                    seen_blocks_recompiled = {}  # Map (start_addr, end_addr) -> basic_block
                    seen_line_ranges_recompiled = []  # List of (start_line, end_line) tuples for already output Basic Blocks
                    
                    # Collect all changed instruction addresses for marking
                    changed_addresses_int_recompiled = set()  # Store as integers for reliable comparison
                    changed_line_numbers_recompiled = set()
                    
                    # Read the recompiled disassembly file to get line-by-line access
                    with open(recompiled_disas_file, "r") as f:
                        recompiled_lines = f.readlines()
                    
                    # First pass: collect all changed addresses and line numbers
                    for line, offset, recompiled_line_num in changed_instructions_recompiled:
                        # Skip diff header lines (---, +++, @@, etc.)
                        if (line.startswith('---') or line.startswith('+++') or 
                            line.startswith('@@') or not line.strip()):
                            continue
                        
                        # Extract address from the line
                        addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
                        if addr_match:
                            addr_str = addr_match.group(1)
                            try:
                                addr_int = int(addr_str, 16)
                                changed_addresses_int_recompiled.add(addr_int)
                                if recompiled_line_num:
                                    changed_line_numbers_recompiled.add(recompiled_line_num)
                            except ValueError:
                                pass
                    
                    # Second pass: extract Basic Blocks
                    for line, offset, recompiled_line_num in changed_instructions_recompiled:
                        # Skip diff header lines (---, +++, @@, etc.)
                        if (line.startswith('---') or line.startswith('+++') or 
                            line.startswith('@@') or not line.strip()):
                            continue
                        
                        # Extract address from the line (format: "+   3:  be c8 00 00 00")
                        addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
                        if not addr_match:
                            continue
                        
                        addr_str = addr_match.group(1)
                        
                        # Use the line number from recompiled file
                        if recompiled_line_num is None or recompiled_line_num < 1 or recompiled_line_num > len(recompiled_lines):
                            print_color(
                                f"Invalid line number {recompiled_line_num} for address 0x{addr_str}",
                                "yellow"
                            )
                            continue
                        
                        # Check if this line is already covered by a previously output Basic Block
                        already_covered = False
                        for start_line, end_line in seen_line_ranges_recompiled:
                            if start_line <= recompiled_line_num <= end_line:
                                already_covered = True
                                break
                        
                        if already_covered:
                            # Skip this instruction as it's already in a Basic Block we've output
                            continue
                        
                        # Step 1: Get the instruction line from recompiled file using line number from diff
                        inst_line_content = recompiled_lines[recompiled_line_num - 1].strip()
                        
                        # Step 2: Find basic block starting from this specific line number
                        # Parse all instructions with their line numbers
                        instructions = parse_instructions_from_disassembly(recompiled_disas_file)
                        
                        # Find the instruction at the target line number
                        target_inst_idx = None
                        for i, (addr, inst_line, is_label, line_num) in enumerate(instructions):
                            if line_num == recompiled_line_num:
                                target_inst_idx = i
                                break
                        
                        if target_inst_idx is None:
                            print_color(
                                f"Could not find instruction at line {recompiled_line_num}",
                                "yellow"
                            )
                            continue
                        
                        # Find basic block boundaries starting from this instruction
                        # Go backwards to find basic block start
                        start_idx = target_inst_idx
                        for i in range(target_inst_idx, -1, -1):
                            addr, inst_line, is_label, line_num = instructions[i]
                            
                            # If this is a label (function start), it's a basic block start
                            if is_label:
                                start_idx = i
                                break
                            
                            # Extract mnemonic
                            mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
                            
                            # Check if this is a basic block terminator
                            if is_basic_block_terminator(mnemonic):
                                # This instruction ends a basic block, start from next one
                                if i + 1 < len(instructions):
                                    start_idx = i + 1
                                else:
                                    start_idx = target_inst_idx
                                break
                            
                            start_idx = i
                        
                        # Go forwards to find basic block end
                        end_idx = start_idx
                        for i in range(start_idx, len(instructions)):
                            addr, inst_line, is_label, line_num = instructions[i]
                            
                            # If this is a label and it's not the start, it's a new basic block
                            if is_label and i > start_idx:
                                end_idx = i - 1
                                break
                            
                            # Extract mnemonic
                            mnemonic = extract_mnemonic(f"  {addr}: {inst_line}")
                            
                            # Check if this is a basic block terminator
                            if is_basic_block_terminator(mnemonic):
                                end_idx = i
                                break
                            
                            end_idx = i
                        
                        # Extract the basic block
                        basic_block = []
                        bb_start_line = None
                        bb_end_line = None
                        for i in range(start_idx, end_idx + 1):
                            addr, inst_line, is_label, line_num = instructions[i]
                            basic_block.append((addr, inst_line))
                            if bb_start_line is None:
                                bb_start_line = line_num
                            bb_end_line = line_num
                        
                        if basic_block:
                            block_key = get_basic_block_key(basic_block)
                            if block_key and block_key not in seen_blocks_recompiled:
                                seen_blocks_recompiled[block_key] = basic_block
                                # Record the line number range for this Basic Block
                                if bb_start_line and bb_end_line:
                                    seen_line_ranges_recompiled.append((bb_start_line, bb_end_line))
                                
                                # Find the function name for this Basic Block
                                # Look backwards from bb_start_line in the file to find function definition
                                function_name = None
                                section_name = None
                                
                                # Search backwards from bb_start_line to find function definition
                                for line_idx in range(bb_start_line - 1, -1, -1):
                                    if line_idx >= len(recompiled_lines):
                                        break
                                    line_content = recompiled_lines[line_idx]
                                    
                                    # Check for function definition: "  address: <function_name>:"
                                    func_match = re.match(
                                        r'^\s*([0-9a-fA-F]+)\s+<([^>]+)>:',
                                        line_content
                                    )
                                    if func_match:
                                        func_addr = func_match.group(1)
                                        func_name = func_match.group(2)
                                        # Skip prefix functions
                                        # if not func_name.startswith('__pfx_') and not func_name.endswith('.cold'):
                                        function_name = func_name
                                        
                                        # Also try to find section name
                                        # Look backwards for section header
                                        for j in range(line_idx - 1, -1, -1):
                                            if j < len(recompiled_lines):
                                                section_line = recompiled_lines[j]
                                                section_match = re.match(
                                                    r'^Disassembly of section (\.text[^:]+):',
                                                    section_line
                                                )
                                                if section_match:
                                                    section_name = section_match.group(1)
                                                    break
                                        break
                                    
                                    # Stop if we hit a section header (went too far back)
                                    if re.match(r'^Disassembly of section', line_content):
                                        break
                                
                                print_color(
                                    f"Basic Block: lines {bb_start_line}-{bb_end_line}",
                                    "yellow"
                                )
                                if function_name:
                                    print(f"Function: {function_name}")
                                else:
                                    print(f"Function: Not found")
                                
                                for addr, inst_line in basic_block:
                                    # Mark changed instructions with [*]
                                    # Convert address to integer for comparison
                                    try:
                                        addr_int = int(addr, 16)
                                        if addr_int in changed_addresses_int_recompiled:
                                            print(f"  [*] {addr}:  {inst_line}")
                                        else:
                                            print(f"  {addr}:  {inst_line}")
                                    except ValueError:
                                        # If address parsing fails, output without mark
                                        print(f"  {addr}:  {inst_line}")
                        else:
                            print_color(
                                f"Could not find Basic Block for line {recompiled_line_num}",
                                "yellow"
                            )
                
                # Find function information for each changed instruction
                print_color(
                    "\n12. Finding function information for changed instructions...",
                    "blue"
                )
                functions = parse_functions_from_disassembly(original_disas_file)
                
                for line, offset, diff_line_number in changed_instructions:
                    if not offset or offset == '':
                        addr_match = re.search(r'^\s*[-+]\s+([0-9a-fA-F]+):', line)
                        if addr_match:
                            offset = addr_match.group(1)
                    
                    func_info = find_function_for_address(
                        functions, offset, original_disas_file, diff_line_number
                    )
                    if func_info:
                        func_name, start_addr, end_addr, size, instruction_count = func_info
                        print(
                            f"{line}\tFunction: {func_name}, Start: 0x{start_addr}, "
                            f"End: 0x{end_addr}, Size: {size} bytes, "
                            f"Instructions: {instruction_count}"
                        )
                    else:
                        print(f"{line}\tFunction: Not found (offset: {offset})")

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
