#!/usr/bin/env python3
"""
Parse IR diff and extract information about changed instructions.

Usage:
    python parse_ir_diff.py <diff_file> <ll_file>
"""

import sys
import re
from pathlib import Path


def parse_diff(diff_content):
    """
    Parse diff content and extract IR instructions with their changed values.
    Returns a list of tuples: (instruction, old_value, new_value)
    """
    lines = diff_content.strip().split('\n')
    results = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for diff change markers (e.g., "597c597")
        if re.match(r'^\d+c\d+$', line):
            i += 1
            if i < len(lines) and lines[i].strip().startswith('<'):
                old_line = lines[i].strip()[1:].strip()  # Remove '<' prefix
                i += 1

                # Skip separator line
                if i < len(lines) and lines[i].strip() == '---':
                    i += 1

                # Get new line
                if i < len(lines) and lines[i].strip().startswith('>'):
                    new_line = lines[i].strip()[1:].strip()  # Remove '>' prefix

                    # Extract constant values from both lines
                    # Match patterns like ", 40," or "i32 40)" or " 40, !dbg"
                    old_match = re.search(r'(?:,|\s)\s*(\d+)\s*[,)]', old_line)
                    new_match = re.search(r'(?:,|\s)\s*(\d+)\s*[,)]', new_line)

                    if old_match and new_match:
                        old_value = old_match.group(1)
                        new_value = new_match.group(1)
                        results.append((old_line, old_value, new_value))

        i += 1

    return results


def find_function_for_instruction(ll_file_path, instruction):
    """
    Find which function contains the given IR instruction.
    Returns the function name or None if not found.
    """
    with open(ll_file_path, 'r') as f:
        content = f.read()

    # For instructions with variable assignments (e.g., "%28 = or...")
    var_match = re.match(r'^\s*(%\d+)\s*=', instruction)
    if var_match:
        var_name = var_match.group(1)
        search_pattern = f"{var_name} ="
    else:
        # For instructions without assignments (e.g., "store i32 200, ptr...")
        # Extract a unique part of the instruction to search for
        # For store instructions, use the opcode and first few tokens
        parts = instruction.split()
        if len(parts) >= 3:
            # Use first 3 tokens as search pattern (e.g., "store i32 200")
            search_pattern = ' '.join(parts[:3])
        else:
            search_pattern = instruction

    # Split by function definitions
    lines = content.split('\n')
    current_function = None

    for line in lines:
        # Check if this is a function definition
        func_match = re.search(r'define\s+[^@]*@([a-zA-Z0-9_\.]+)\s*\(', line)
        if func_match:
            current_function = func_match.group(1)

        # Check if the search pattern appears in this line
        if search_pattern in line:
            return current_function

    return None


def extract_opcode(instruction):
    """Extract the opcode from an IR instruction."""
    # Pattern 1: %var = [tail] call ... (handle special case for tail call)
    match = re.search(r'%\d+\s*=\s*(?:tail\s+)?(call)', instruction)
    if match:
        return match.group(1)

    # Pattern 2: %var = opcode ... (e.g., "%6 = icmp ...")
    match = re.search(r'%\d+\s*=\s*(\w+)', instruction)
    if match:
        return match.group(1)

    # Pattern 3: opcode at the start (e.g., "store i32 200, ...")
    match = re.match(r'^\s*(\w+)', instruction)
    if match:
        return match.group(1)

    return None


def ll_to_c_path(ll_path):
    """Convert .ll path to .c path."""
    path = Path(ll_path)

    # Extract the relative path part after the build directory
    # Example: ../linux-wllvm-defconfig/net/ipv4/tcp_output.ll -> net/ipv4/tcp_output.c
    parts = path.parts

    # Find where the actual source path starts (after build directory name)
    for i, part in enumerate(parts):
        if 'linux' in part.lower() or part.startswith('.'):
            continue
        else:
            # Reconstruct path from here
            source_parts = parts[i:]
            source_path = Path(*source_parts)
            return str(source_path.with_suffix('.c'))

    # Fallback: just change extension
    return str(path.with_suffix('.c'))


def main():
    if len(sys.argv) != 3:
        print("Usage: python parse_ir_diff.py <diff_file> <ll_file>")
        sys.exit(1)

    diff_file = sys.argv[1]
    ll_file = sys.argv[2]

    # Read diff content
    with open(diff_file, 'r') as f:
        diff_content = f.read()

    # Parse diff
    instructions = parse_diff(diff_content)

    # Convert ll path to c path
    source_file = ll_to_c_path(ll_file)

    # Process each instruction
    for instruction, old_value, new_value in instructions:
        function_name = find_function_for_instruction(ll_file, instruction)
        opcode = extract_opcode(instruction)

        # Output in the requested format
        print(f"# # {instruction}")
        print(f"# # Conclusion: []")
        print(f"#")
        print(f"# SOURCE_FILE={source_file}")
        print(f"# FUNCTION_NAME={function_name if function_name else 'UNKNOWN'}")
        print(f"# SOURCE_OP=\"{opcode if opcode else 'UNKNOWN'}\"")
        print(f"# CONSTANT_VALUE={old_value}")
        print(f"# OCCURENCE=1")
        print()


if __name__ == "__main__":
    main()

