#!/usr/bin/env python3

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys
import os
import glob

@dataclass
class Span:
    """Represents a data flow span in a function."""
    start_bb: int
    start_inst: int
    end_bb: int
    end_inst: int

    def __repr__(self):
        return f"BB{self.start_bb}:I{self.start_inst} -> BB{self.end_bb}:I{self.end_inst}"


@dataclass
class FunctionInfo:
    """Information about a function's data flow."""
    name: str
    full_span: bool
    spans: List[Span] = None  # Multiple spans

    def __post_init__(self):
        if self.spans is None:
            self.spans = []

    def __repr__(self):
        if self.full_span:
            return f"{self.name}: full span"
        elif len(self.spans) == 0:
            return f"{self.name}: no spans"
        elif len(self.spans) == 1:
            return f"{self.name}: {self.spans[0]}"
        else:
            spans_str = ", ".join(str(s) for s in self.spans)
            return f"{self.name}: [{spans_str}]"


def parse_span_details(output_file: str) -> Dict[str, FunctionInfo]:
    """
    Parse the Data Flow Span Details section from analysis output.

    Returns:
        Dictionary mapping function name to FunctionInfo
    """
    results = {}
    in_span_section = False

    with open(output_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Detect start of span details section
            if "=== Data Flow Span Details ===" in line:
                in_span_section = True
                continue

            # Detect end of section
            if in_span_section and line.startswith("==="):
                break

            # Parse span lines
            if in_span_section and line and ',' in line:
                parts = [p.strip() for p in line.split(',')]
                func_name = parts[0]

                if len(parts) == 2 and parts[1] == "full span":
                    results[func_name] = FunctionInfo(func_name, full_span=True, spans=[])
                elif len(parts) == 5:
                    span = Span(
                        start_bb=int(parts[1]),
                        start_inst=int(parts[2]),
                        end_bb=int(parts[3]),
                        end_inst=int(parts[4])
                    )
                    results[func_name] = FunctionInfo(func_name, full_span=False, spans=[span])

    return results


def compare_position(bb1: int, inst1: int, bb2: int, inst2: int) -> int:
    """
    Compare two positions (BB, instruction).
    Returns: -1 if pos1 < pos2, 0 if equal, 1 if pos1 > pos2
    """
    if bb1 < bb2:
        return -1
    elif bb1 > bb2:
        return 1
    else:  # same BB
        if inst1 < inst2:
            return -1
        elif inst1 > inst2:
            return 1
        else:
            return 0


def spans_overlap_or_adjacent(span1: Span, span2: Span) -> bool:
    """
    Check if two spans overlap or are adjacent (touching).
    Spans are considered adjacent if one ends right before the other starts.
    """
    # Make sure span1 starts before or at span2
    if compare_position(span1.start_bb, span1.start_inst,
                       span2.start_bb, span2.start_inst) > 0:
        span1, span2 = span2, span1

    # Check if span1's end is at or after span2's start
    # (or within 1 instruction - to handle adjacency)
    end_cmp = compare_position(span1.end_bb, span1.end_inst,
                               span2.start_bb, span2.start_inst)

    # Overlapping if span1 ends at or after span2 starts
    # We consider them adjacent even if there's a small gap (same BB, consecutive instructions)
    if end_cmp >= 0:
        return True

    # Check for adjacency in same BB
    if span1.end_bb == span2.start_bb and span2.start_inst - span1.end_inst <= 1:
        return True

    return False


def merge_two_spans(span1: Span, span2: Span) -> Span:
    """
    Merge two overlapping or adjacent spans into one.
    Takes the earliest start and latest end.
    """
    # Determine earliest start
    if compare_position(span1.start_bb, span1.start_inst,
                       span2.start_bb, span2.start_inst) <= 0:
        start_bb, start_inst = span1.start_bb, span1.start_inst
    else:
        start_bb, start_inst = span2.start_bb, span2.start_inst

    # Determine latest end
    if compare_position(span1.end_bb, span1.end_inst,
                       span2.end_bb, span2.end_inst) >= 0:
        end_bb, end_inst = span1.end_bb, span1.end_inst
    else:
        end_bb, end_inst = span2.end_bb, span2.end_inst

    return Span(start_bb, start_inst, end_bb, end_inst)


def union_span_lists(span_lists: List[List[Span]]) -> List[Span]:
    """
    Union multiple lists of spans, keeping non-overlapping spans separate.

    Example: [1-2], [5-8], [7-9] becomes [[1-2], [5-9]]
    """
    # Collect all spans
    all_spans = []
    for span_list in span_lists:
        all_spans.extend(span_list)

    if not all_spans:
        return []

    # Sort spans by start position
    all_spans.sort(key=lambda s: (s.start_bb, s.start_inst))

    # Merge overlapping/adjacent spans
    merged = [all_spans[0]]

    for current_span in all_spans[1:]:
        last_merged = merged[-1]

        if spans_overlap_or_adjacent(last_merged, current_span):
            # Merge with the last span in merged list
            merged[-1] = merge_two_spans(last_merged, current_span)
        else:
            # Add as a separate span
            merged.append(current_span)

    return merged


def union_results(results_list: List[Dict[str, FunctionInfo]]) -> Dict[str, FunctionInfo]:
    """
    Union multiple analysis results.

    For each function:
    - If marked as "full span" in any result, it's full span in union
    - Otherwise, union all partial spans, keeping non-overlapping spans separate

    Example: [1-2] U [5-8] U [7-9] becomes [[1-2], [5-9]]
    """
    all_functions = set()
    for results in results_list:
        all_functions.update(results.keys())

    union = {}

    for func_name in all_functions:
        # Collect all info for this function across runs
        func_infos = [r[func_name] for r in results_list if func_name in r]

        # If any result has full span, the union is full span
        if any(fi.full_span for fi in func_infos):
            union[func_name] = FunctionInfo(func_name, full_span=True, spans=[])
        else:
            # Collect all span lists
            span_lists = [fi.spans for fi in func_infos if fi.spans]
            if span_lists:
                merged_spans = union_span_lists(span_lists)
                union[func_name] = FunctionInfo(func_name, full_span=False, spans=merged_spans)

    return union


def print_results(results: Dict[str, FunctionInfo], title: str = "Results"):
    """Print results in a readable format."""
    # print(f"\n{title}")
    # print("=" * len(title))
    for func_name in sorted(results.keys()):
        print(f"  {results[func_name]}")

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: python union-ss.py kernel-results/<perf-const name>")
        sys.exit(1)

    dir_name = sys.argv[1]

    if (not os.path.exists(dir_name)):
        print(f"Directory {dir_name} does not exist")
        sys.exit(1)

    result_files = glob.glob(os.path.join(dir_name, "*.output.txt"))
    if (len(result_files) == 0):
        print(f"No result files found in {dir_name}")
        sys.exit(1)

    results = []
    for result_file in result_files:

        results.append(parse_span_details(result_file))
        # print_results(results[-1])

    union = union_results(results)
    print_results(union)

