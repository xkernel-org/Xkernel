import os
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from collections import defaultdict
import argparse
from skip import skip_keywords, skip_paths

parser = argparse.ArgumentParser(description='Extract constants from Linux kernel source code')
parser.add_argument('--src', type=str, default='../linux-6.14.7', help='Path to Linux kernel source code')
parser.add_argument('--output', type=str, default='./constants_table.csv', help='Path to output CSV file')
parser.add_argument('--workers', type=int, default=16, help='Number of worker threads')
parser.add_argument('--summary_only', action='store_true', help='Whether to output summary only')
parser.add_argument('--subsystem', type=str, default='', help='Subsystem to analyze', choices=["arch", "drivers", "fs", "init", "ipc", "kernel", "mm", "net", "other", "security", "sound"])
args = parser.parse_args()

LINUX_SRC = args.src
OUTPUT_FILE = args.output
MAX_WORKERS = args.workers
SUMMARY_OUTPUT_FILE = "./constants_summary.csv"

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
    # Read all rows first with progress bar
    with open(csv_file_path, "r", encoding="utf-8") as f:
        # Get total number of lines for progress bar
        total_lines = sum(1 for _ in f)
        f.seek(0)  # Reset file pointer
        
        reader = csv.DictReader(f)
        rows = []
        for row in tqdm(reader, total=total_lines-1, desc="Reading CSV"):  # -1 for header
            rows.append(row)

    # Split rows into chunks
    chunk_size = max(1, len(rows) // MAX_WORKERS)
    chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]

    # Process chunks in parallel
    summaries = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Analyzing constants"):
            summaries.append(future.result())

    # Merge results
    summary = merge_summaries(summaries)

    # Print results
    print(f"\n{'Subsystem':<12} | {'Total':<10} | {'Macros':<10} | {'Static Consts'}")
    print("-" * 45)
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

define_pattern = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(.+)$')
static_const_pattern = re.compile(r'^\s*static\s+const\s+[\w\s\*]+\s+([a-zA-Z0-9_]+)\s*=\s*(.+);')

def get_subsystem(path):
    parts = path.split(os.sep)
    for part in parts:
        if part in {"fs", "mm", "net", "kernel", "drivers", "arch", "init", "ipc", "security", "sound"}:
            return part
    return "other"

def filter_constants(name, filter_keywords):
    return any(keyword.lower() in name.lower() for keyword in filter_keywords)

def should_skip_constant(name):
    return filter_constants(name, skip_keywords)

def process_file(full_path):
    # filter all the files in the above list
    if any(path in full_path for path in skip_paths):
        return []
        
    results = []
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                match1 = define_pattern.match(line)
                match2 = static_const_pattern.match(line)
                if match1:
                    name, value = match1.groups()
                    if should_skip_constant(name):
                        continue
                    results.append([
                        get_subsystem(full_path),
                        full_path,
                        i + 1,
                        "macro",
                        name,
                        value.strip(),
                        ""
                    ])
                elif match2:
                    name, value = match2.groups()
                    if should_skip_constant(name):
                        continue
                    results.append([
                        get_subsystem(full_path),
                        full_path,
                        i + 1,
                        "static_const",
                        name,
                        value.strip(),
                        ""
                    ])
    except Exception as e:
        print(f"Failed to read {full_path}: {e}")
    return results

def analyze_constants_multithreaded():
    files_to_process = []
    for root, _, files in os.walk(LINUX_SRC):
        # Skip selftests directory
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
                print(f"Exception in future: {e}")
    return results

def save_to_csv(data, output_file):
    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Subsystem", "File Path", "Line Number", "Type", "Name", "Value", "Description"])
        writer.writerows(data)
    print(f"\nSaved result to: {OUTPUT_FILE}")

def save_to_csv_subsystem(subsystem):
    with open(OUTPUT_FILE, "r", newline='') as f:
        reader = csv.reader(f)
        next(reader)
        
        with open(f"{subsystem}_constants.csv", "w", newline='') as out:
            writer = csv.writer(out)
            writer.writerow(["Subsystem", "File Path", "Line Number", "Type", "Name", "Value", "Description"])
            for row in reader:
                if row[0] == subsystem:
                    writer.writerow(row)
    print(f"Saved {subsystem} constants to {subsystem}_constants.csv")

if __name__ == "__main__":
    if args.summary_only:
        analyze_constants_summary(OUTPUT_FILE)
    else:
        constants = analyze_constants_multithreaded()
        save_to_csv(constants, OUTPUT_FILE)
        analyze_constants_summary(OUTPUT_FILE)

    if args.subsystem:
        save_to_csv_subsystem(args.subsystem)
    