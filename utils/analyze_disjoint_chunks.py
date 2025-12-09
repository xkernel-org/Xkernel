#!/usr/bin/env python3
"""
Analyze disjoint chunks in addr.csv based on ID, function, and offset ranges.
"""

import csv
import sys
from collections import defaultdict
from typing import List, Tuple, Dict


def parse_offset(offset_str: str) -> Tuple[int, int]:
    """
    Parse offset string like "0x297 - 0x2a1" into (start, end) tuple.
    Returns (start, end) as integers.
    """
    parts = offset_str.strip().split(' - ')
    if len(parts) != 2:
        raise ValueError(f"Invalid offset format: {offset_str}")

    start = int(parts[0], 16)
    end = int(parts[1], 16)
    return (start, end)


def ranges_overlap(range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
    """
    Check if two ranges overlap.
    """
    start1, end1 = range1
    start2, end2 = range2

    # Ensure start <= end for both ranges
    if start1 > end1:
        start1, end1 = end1, start1
    if start2 > end2:
        start2, end2 = end2, start2

    # Check for overlap
    return not (end1 < start2 or end2 < start1)


def merge_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merge overlapping ranges into disjoint chunks.
    """
    if not ranges:
        return []

    # Normalize ranges (ensure start <= end)
    normalized = []
    for start, end in ranges:
        if start > end:
            start, end = end, start
        normalized.append((start, end))

    # Sort by start position
    sorted_ranges = sorted(normalized, key=lambda x: x[0])

    # Merge overlapping ranges
    merged = [sorted_ranges[0]]

    for current in sorted_ranges[1:]:
        last = merged[-1]

        if ranges_overlap(last, current):
            # Merge the ranges
            merged[-1] = (min(last[0], current[0]), max(last[1], current[1]))
        else:
            # Add as new disjoint range
            merged.append(current)

    return merged


def analyze_csv(csv_file: str) -> Dict[str, List[List[dict]]]:
    """
    Analyze the CSV file and return disjoint chunks for each ID.

    Returns:
        Dictionary mapping ID to list of disjoint chunks, where each chunk
        is a list of row dictionaries.
    """
    # Read CSV file
    rows_by_id = defaultdict(list)

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ID'].strip():  # Skip empty rows
                rows_by_id[row['ID']].append(row)

    # Analyze each ID
    results = {}

    for id_val, rows in sorted(rows_by_id.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        # Group by function
        rows_by_function = defaultdict(list)

        for row in rows:
            function = row['function']
            rows_by_function[function].append(row)

        # Process each function group
        all_chunks = []

        for function, func_rows in rows_by_function.items():
            # Extract offset ranges
            ranges_with_rows = []
            for row in func_rows:
                try:
                    offset_range = parse_offset(row['offset'])
                    ranges_with_rows.append((offset_range, row))
                except ValueError as e:
                    print(f"Warning: Skipping row with invalid offset: {e}", file=sys.stderr)
                    continue

            if not ranges_with_rows:
                continue

            # Sort by range start
            ranges_with_rows.sort(key=lambda x: min(x[0][0], x[0][1]))

            # Merge overlapping ranges within same function
            current_chunk = [ranges_with_rows[0][1]]
            current_range = ranges_with_rows[0][0]

            for (offset_range, row) in ranges_with_rows[1:]:
                if ranges_overlap(current_range, offset_range):
                    # Add to current chunk and extend range
                    current_chunk.append(row)
                    start = min(current_range[0], current_range[1], offset_range[0], offset_range[1])
                    end = max(current_range[0], current_range[1], offset_range[0], offset_range[1])
                    current_range = (start, end)
                else:
                    # Start new chunk
                    all_chunks.append(current_chunk)
                    current_chunk = [row]
                    current_range = offset_range

            # Add the last chunk
            all_chunks.append(current_chunk)

        results[id_val] = all_chunks

    return results


def format_chunk(chunk: List[dict]) -> str:
    """
    Format a chunk for display.
    """
    entries = []
    for row in chunk:
        entry = f"{row['function']}:{row['offset']}"
        entries.append(entry)
    return f"[{', '.join(entries)}]"


def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = 'find-binary-addresses/addr.csv'

    try:
        results = analyze_csv(csv_file)

        for id_val, chunks in results.items():
            chunk_strs = [format_chunk(chunk) for chunk in chunks]
            chunks_repr = ', '.join(chunk_strs)
            print(f"{id_val}, {len(chunks)}, \"[{chunks_repr}]\"")

    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

