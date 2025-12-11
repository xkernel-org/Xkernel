#!/usr/bin/env python3

"""
Script to calculate span instruction sizes from BB1:I1 -> BB2:I2 notation.
Takes vmlinux-func-bb-sizes.txt and kernel-results/*/ss-size1.txt files to produce
kernel-results/*/ss-size2.txt files.
"""

import sys
import re
import os
from pathlib import Path
from collections import defaultdict

def parse_vmlinux_func_bb_sizes(vmlinux_func_bb_sizes_file):
    """
    Returns two dicts:
    - bb_sizes: {function_name: {bb_index: instruction_count}}
    - function_totals: {function_name: total_instruction_count}
    """
    bb_sizes = defaultdict(dict)
    function_totals = {}
    current_function = None

    with open(vmlinux_func_bb_sizes_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Match function line: "Function: function_name"
            func_match = re.match(r'Function:\s+(\S+)', line)
            if func_match:
                current_function = func_match.group(1)
                total_instructions_double_check = 0
                num_bbs_double_check = 0
                continue

            # Match BB line: "  BB0: 8" or "  BB0 (label): 8 instructions"
            bb_match = re.match(r'\s*BB(\d+)(?:\s+\([^)]+\))?\s*:\s*(\d+)', line)
            if bb_match and current_function:
                bb_index = int(bb_match.group(1))
                instruction_count = int(bb_match.group(2))
                bb_sizes[current_function][bb_index] = instruction_count
                total_instructions_double_check += instruction_count
                num_bbs_double_check += 1

            # Match Total line: "  Total: X basic blocks, Y instructions"
            total_match = re.match(r'\s*Total:\s+(\d+)\s+basic blocks,\s+(\d+)\s+instructions', line)
            if total_match and current_function:
                num_bbs = int(total_match.group(1))
                total_instructions = int(total_match.group(2))
                function_totals[current_function] = total_instructions

                assert total_instructions_double_check == total_instructions
                assert num_bbs_double_check == num_bbs

    return bb_sizes, function_totals


def calculate_span_size(bb_sizes, function, start_bb, start_i, end_bb, end_i):
    """
    Calculate the number of instructions in a span from BB_start:I_start to BB_end:I_end.

    The span includes:
    - Instructions from I_start to end of BB_start (inclusive)
    - All instructions in BBs between start_bb and end_bb
    - Instructions from beginning of BB_end to I_end (inclusive)

    Note: Instruction indices are 0-based in LLVM.
    """
    if function not in bb_sizes:
        return None, f"Function '{function}' not found in BB size data"

    func_bbs = bb_sizes[function]

    # Check if start and end BBs exist
    if start_bb not in func_bbs:
        return None, f"BB{start_bb} not found in function '{function}'"
    if end_bb not in func_bbs:
        return None, f"BB{end_bb} not found in function '{function}'"

    total_size = 0

    if start_bb == end_bb:
        # Same basic block: just count from start_i to end_i (inclusive)
        size = end_i - start_i + 1
        if size < 0:
            return None, f"Invalid span: start instruction {start_i} is after end instruction {end_i}"
        return size, None

    # Count instructions from start_i to end of start_bb
    start_bb_size = func_bbs[start_bb]
    if start_i >= start_bb_size:
        return None, f"Start instruction I{start_i} is out of bounds for BB{start_bb} (size: {start_bb_size})"
    total_size += start_bb_size - start_i

    # Count all instructions in intermediate BBs
    for bb_idx in range(start_bb + 1, end_bb):
        if bb_idx in func_bbs:
            total_size += func_bbs[bb_idx]
        else:
            assert False

    # Count instructions from beginning of end_bb to end_i (inclusive)
    end_bb_size = func_bbs[end_bb]
    if end_i >= end_bb_size:
        return None, f"End instruction I{end_i} is out of bounds for BB{end_bb} (size: {end_bb_size})"
    total_size += end_i + 1

    return total_size, None


def process_ss_size1_file(ss_size1_file, bb_sizes, function_totals, output_file):
    """
    Process a single ss-size1.txt file and write results to ss-size2.txt.
    """
    results = []

    with open(ss_size1_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("Input files: ") or \
               line.startswith("Total input spans: ") or \
               line.startswith("Total output clusters: ") or \
               line.startswith("Reduction: ") or \
               line.startswith("Virtual files (after merging): ") or \
               line.startswith("File reduction: "):
                continue

            # Parse line: "  function_name: full span"
            full_span_match = re.match(r'\s*(\S+):\s+full span', line)
            if full_span_match:
                function = full_span_match.group(1)
                if function in function_totals:
                    size = function_totals[function]
                    results.append((line, size, None))
                else:
                    results.append((line, None, f"Function '{function}' not found in BB size data"))
                    assert False
                continue

            # Parse line: "  function_name: [BB:I -> BB:I, BB:I -> BB:I, ...]"
            multi_span_match = re.match(r'\s*(\S+):\s+\[(.*?)\]', line)
            if multi_span_match:
                function = multi_span_match.group(1)
                spans_str = multi_span_match.group(2)

                # Split by comma and parse each span
                span_list = [s.strip() for s in spans_str.split(',')]
                total_size = 0
                errors = []

                for span in span_list:
                    # Parse each span: BB:I -> BB:I
                    span_match = re.match(r'BB(\d+):I(\d+)\s*->\s*BB(\d+):I(\d+)', span)
                    if span_match:
                        start_bb = int(span_match.group(1))
                        start_i = int(span_match.group(2))
                        end_bb = int(span_match.group(3))
                        end_i = int(span_match.group(4))

                        size, error = calculate_span_size(bb_sizes, function, start_bb, start_i, end_bb, end_i)
                        if size is not None and error is None:
                            total_size += size
                        else:
                            errors.append(f"{span}: {error}")
                            assert False
                    else:
                        errors.append(f"{span}: Invalid span format")
                        assert False

                if errors:
                    results.append((line, None, "; ".join(errors)))
                    assert False
                else:
                    results.append((line, total_size, None))
                continue

            # Parse line: "  function_name: BB2:I4 -> BB11:I2"
            match = re.match(r'\s*(\S+):\s+BB(\d+):I(\d+)\s*->\s*BB(\d+):I(\d+)', line)
            if not match:
                # Keep original line if it doesn't match the pattern
                results.append((line, None, "Invalid format"))
                assert False

            function = match.group(1)
            start_bb = int(match.group(2))
            start_i = int(match.group(3))
            end_bb = int(match.group(4))
            end_i = int(match.group(5))

            # Calculate size
            size, error = calculate_span_size(bb_sizes, function, start_bb, start_i, end_bb, end_i)

            if error is not None:
                assert False
            results.append((line, size, error))

    # Calculate total instructions
    total_instructions = sum(size for _, size, error in results if size is not None and error is None)

    # Write results
    with open(output_file, 'w') as f:
        for original_line, size, error in results:
            if size is not None:
                f.write(f"{original_line} => {size} instructions\n")
            else:
                f.write(f"{original_line} => ERROR: {error}\n")
                assert False

        # Add total at the end
        if results:
            f.write(f"\nTotal: {total_instructions} instructions\n")

    print(f"Processed {ss_size1_file} -> {output_file}")
    return len(results)


def main():
    if len(sys.argv) != 2:
        print("Usage: python character-ss-size-from-spans.py <vmlinux-func-bb-sizes.txt>")
        print()
        print("This script reads:")
        print("  1. vilinux function BB size file (output from BBSizePass)")
        print("  2. All kernel-results*/*/ss-size1.txt files")
        print()
        print("And produces:")
        print("  kernel-results*/*/ss-size2.txt files with calculated instruction counts")
        print()
        print("Supports:")
        print("  - 'BB:I -> BB:I' notation for specific spans")
        print("  - 'full span' notation for entire function size")
        print("  - Adds total instruction count at end of each file")
        sys.exit(1)

    vmlinux_func_bb_sizes_file = sys.argv[1]

    if not os.path.exists(vmlinux_func_bb_sizes_file):
        print(f"Error: vmlinux function BB size file '{vmlinux_func_bb_sizes_file}' not found")
        sys.exit(1)

    print(f"Reading vmlinux function BB sizes from {vmlinux_func_bb_sizes_file}...")
    bb_sizes, function_totals = parse_vmlinux_func_bb_sizes(vmlinux_func_bb_sizes_file)
    print(f"Loaded vmlinux function BB size information for {len(bb_sizes)} functions")

    # Find all ss-size1.txt files in kernel-results* subdirectories
    processed_count = 0
    total_spans = 0

    current_dir = Path(".")
    kernel_results_dir = current_dir / 'kernel-results'

    if not kernel_results_dir.exists():
        print("Error: kernel_results directory not found")
        sys.exit(1)

    for ss_file in kernel_results_dir.glob("*/ss-size1.txt"):
        output_file = ss_file.parent / "ss-size2.txt"
        count = process_ss_size1_file(ss_file, bb_sizes, function_totals, output_file)
        processed_count += 1
        total_spans += count

    print(f"\nComplete!")
    print(f"Processed {processed_count} directories")
    print(f"Calculated sizes for {total_spans} total spans")


if __name__ == "__main__":
    main()

