# 1.提取各个子系统(不包含include/下的文件)中的宏
# 2.对各个子系统进行分类, 只提取需要的子系统的宏定义
# 3.对分类之后的宏进行按需求过滤

import os
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from collections import defaultdict
import argparse
# Make sure you have a skip.py file with these lists, or define them here
# Example:
# skip_keywords = ["_IO", "_IOR", "_IOW", "BIT", "GENMASK"]
# skip_paths = ["/arch/riscv/", "/scripts/"]
from skip import skip_keywords, skip_paths

parser = argparse.ArgumentParser(description='Extract constants from Linux kernel source code')
parser.add_argument('--src', type=str, default='/home/spike/linux-6.14.7', help='Path to Linux kernel source code')
parser.add_argument('--output', type=str, default='./constants_table.csv', help='Path to output CSV file')
parser.add_argument('--workers', type=int, default=16, help='Number of worker threads')
parser.add_argument('--summary_only', action='store_true', help='Whether to output summary only')
parser.add_argument('--subsystem', type=str, default='', help='Subsystem to analyze', choices=["block", "fs", "io_uring", "mm", "net", "kernel", "drivers", "arch", "init", "ipc", "security", "sound"])
args = parser.parse_args()

LINUX_SRC = args.src
OUTPUT_FILE = args.output
MAX_WORKERS = args.workers
SUMMARY_OUTPUT_FILE = "./constants_summary.csv"

# --- HELPER FUNCTIONS FOR ANALYSIS (UNCHANGED) ---
def process_chunk(chunk):
    chunk_summary = defaultdict(lambda: {"macro": 0, "static_const": 0})
    for row in chunk:
        subsystem = row["Subsystem"]
        const_type = row["Type"]
        if const_type in ("macro", "static_const"):
            chunk_summary[subsystem][const_type] += 1
    return chunk_summary

def merge_summaries(summaries):
    merged = defaultdict(lambda: {"macro": 0, "static_const": 0})
    for summary in summaries:
        for subsystem, counts in summary.items():
            merged[subsystem]["macro"] += counts["macro"]
            merged[subsystem]["static_const"] += counts["static_const"]
    return merged

def analyze_constants_summary(csv_file_path, output_summary=True):
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}. Cannot generate summary.")
        return
        
    with open(csv_file_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
        f.seek(0)
        reader = csv.DictReader(f)
        rows = list(tqdm(reader, total=max(0, total_lines - 1), desc="Reading CSV"))

    if not rows:
        print("CSV is empty. No summary to generate.")
        return
        
    chunk_size = max(1, len(rows) // MAX_WORKERS)
    chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]
    summaries = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Analyzing constants"):
            summaries.append(future.result())

    summary = merge_summaries(summaries)
    print(f"\n{'Subsystem':<12} | {'Total':<10} | {'Macros':<10} | {'Static Consts'}")
    print("-" * 50)
    for subsystem, counts in sorted(summary.items()):
        total = counts["macro"] + counts["static_const"]
        print(f"{subsystem:<12} | {total:<10} | {counts['macro']:<10} | {counts['static_const']}")

    if output_summary:
        with open(SUMMARY_OUTPUT_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Subsystem", "Total Constants", "Macros", "Static Consts"])
            for subsystem, counts in sorted(summary.items()):
                total = counts["macro"] + counts["static_const"]
                writer.writerow([subsystem, total, counts["macro"], counts["static_const"]])
        print(f"\nSummary saved to: {SUMMARY_OUTPUT_FILE}")

# --- REGEX AND HELPER FUNCTIONS FOR EXTRACTION ---
define_pattern = re.compile(r'^\s*#define\s+([a-zA-Z0-9_]+(?:\(.*\))?)(?:\s+(.+))?$')
static_const_pattern = re.compile(r'^\s*static\s+const\s+[\w\s\*]+\s+([a-zA-Z0-9_]+)\s*=\s*(.+);')

def get_subsystem(path):
    relative_path = os.path.relpath(path, LINUX_SRC)
    parts = relative_path.split(os.sep)
    if not parts: return "other"
    first_dir = parts[0]
    if first_dir in {"block", "fs", "io_uring", "mm", "net", "kernel", "drivers", "arch", "init", "ipc", "security", "sound"}:
        return first_dir
    return "other"

def should_skip_constant(name):
    return any(keyword.lower() in name.lower() for keyword in skip_keywords)

# --- START OF NEW AND MODIFIED FUNCTIONS ---

def get_logical_lines(raw_lines):
    """
    A generator that stitches raw lines ending with a backslash into single, logical lines.
    This correctly handles multi-line macros.
    Yields: (str: logical_line, int: starting_line_number)
    """
    logical_line = ""
    start_line_num = -1
    for i, raw_line in enumerate(raw_lines):
        if not logical_line:
            # This is the start of a new potential logical line
            start_line_num = i + 1

        stripped_line = raw_line.rstrip(' \t\n\r')
        if stripped_line.endswith('\\'):
            # It's a continuation line. Append it, minus the backslash.
            logical_line += stripped_line[:-1] + " "
        else:
            # It's the end of a logical line. Append it and yield.
            logical_line += raw_line.strip()
            # Only yield non-empty lines
            if logical_line:
                yield (logical_line, start_line_num)
            # Reset for the next logical line
            logical_line = ""

def process_file(full_path):
    """
    Processes a single source file to find constants and macros, now with
    robust handling for multi-line definitions.
    """
    if any(path in full_path for path in skip_paths):
        return []
        
    results = []
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Failed to read {full_path}: {e}")
        return []

    # Process the file using logical lines to correctly handle multi-line macros
    for logical_line, line_num in get_logical_lines(lines):
        # Check for a macro definition
        match1 = define_pattern.match(logical_line)
        if match1:
            name, value = match1.groups()
            # value can be None if the macro has no body (e.g., #define FOO)
            value = value or ""
            
            if not should_skip_constant(name):
                results.append([
                    get_subsystem(full_path),
                    full_path,
                    line_num,
                    "macro",
                    name,
                    value.strip(),
                    ""
                ])
            continue # Move to the next logical line

        # Check for a static const definition
        match2 = static_const_pattern.match(logical_line)
        if match2:
            name, value = match2.groups()
            if not should_skip_constant(name):
                results.append([
                    get_subsystem(full_path),
                    full_path,
                    line_num,
                    "static_const",
                    name.strip(),
                    value.strip(),
                    ""
                ])
                
    return results

# --- END OF NEW AND MODIFIED FUNCTIONS ---

def analyze_constants_multithreaded():
    files_to_process = []
    for root, _, files in os.walk(LINUX_SRC):
        if "tools/testing/selftests" in root:
            continue
        for file in files:
            if file.endswith((".c", ".h")):
                full_path = os.path.join(root, file)
                files_to_process.append(full_path)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, path): path for path in files_to_process}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Analyzing files"):
            try:
                results.extend(future.result())
            except Exception as e:
                print(f"Exception processing future for {futures[future]}: {e}")
    return results

def save_to_csv(data, output_file):
    with open(output_file, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Subsystem", "File Path", "Line Number", "Type", "Name", "Value", "Description"])
        writer.writerows(data)
    print(f"\nSaved result to: {output_file}")

def save_to_csv_subsystem(subsystem):
    if not os.path.exists(OUTPUT_FILE):
        print(f"Error: Main output file '{OUTPUT_FILE}' not found.")
        return
        
    output_path = f"./{subsystem}_constants.csv"
    with open(OUTPUT_FILE, "r", newline='', encoding='utf-8') as f, \
         open(output_path, "w", newline='', encoding='utf-8') as out:
        reader = csv.reader(f)
        writer = csv.writer(out)
        header = next(reader)
        writer.writerow(header)
        count = 0
        for row in reader:
            if row and row[0] == subsystem:
                writer.writerow(row)
                count += 1
    print(f"Saved {count} constants for subsystem '{subsystem}' to {output_path}")

if __name__ == "__main__":
    if not os.path.isdir(LINUX_SRC):
        print(f"Error: Linux source directory not found at '{LINUX_SRC}'")
    else:
        if args.summary_only:
            analyze_constants_summary(OUTPUT_FILE)
        else:
            constants = analyze_constants_multithreaded()
            save_to_csv(constants, OUTPUT_FILE)
            analyze_constants_summary(OUTPUT_FILE)

        if args.subsystem:
            save_to_csv_subsystem(args.subsystem)