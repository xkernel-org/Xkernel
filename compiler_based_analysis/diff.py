import sys
import os
import csv

def parse_log_file(filepath):
    """
    Parses the AST analysis log file.

    Args:
        filepath (str): The path to the log file.

    Returns:
        A dictionary mapping (file_path, function_name, variable_name) to a
        tuple of (assigned_value, line_number). It only keeps the last value
        found for a given key.
    """
    assignments = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith("FINDME_INT,"):
                    try:
                        # New format: FINDME_INT,function,lhs,value,macro,location
                        parts = line.strip().split(',', 5)
                        if len(parts) < 6:
                            continue

                        _tag, function_name, lhs, value, _macro_name, location = parts

                        # Extract file path and line number from location string
                        # (e.g., path/to/file.c:123:45)
                        location_parts = location.split(':')
                        file_path = location_parts[0]
                        line_number = location_parts[1] if len(location_parts) > 1 else 'N/A'

                        # Key is (file_path, function_name, variable_name)
                        key = (file_path, function_name, lhs)
                        assignments[key] = (value, line_number)
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        pass
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}", file=sys.stderr)
        sys.exit(1)

    return assignments

def main():
    if len(sys.argv) != 4:
        print("Usage: python diff.py <log_file_v1> <log_file_v2> <csv_output>")
        print("\nCompares two analysis logs to find variables with changed constant values.")
        print("Example: python diff.py log_dir/log-5.15/all.txt.1 log_dir/log-6.15/all.txt.1 diff-5.15-6.15.csv")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    csv_file_path = sys.argv[3]

    # Deriving version prefixes from log file paths
    # e.g. "log_dir/log-6.15/all.txt.1" -> "log_dir/log-6.15" -> "kernel_build_dir/linux-6.15"
    def get_version_prefix(log_path):
        return os.path.dirname(log_path.replace('log_dir/log-', 'kernel_build_dir/linux-', 1))


    prefix1 = get_version_prefix(file1_path)
    prefix2 = get_version_prefix(file2_path)

    print(f"Parsing {file1_path} (version: {prefix1})...")
    assignments1 = parse_log_file(file1_path)
    print(f"Found {len(assignments1)} assignments in {file1_path}.")

    print(f"\nParsing {file2_path} (version: {prefix2})...")
    assignments2 = parse_log_file(file2_path)
    print(f"Found {len(assignments2)} assignments in {file2_path}.")

    print("\nComparing assignments...")

    changed_values = []

    # Iterate through assignments in the first version
    for key, data1 in assignments1.items():
        # Check if the same assignment exists in the second version
        if key in assignments2:
            data2 = assignments2[key]
            value1, line1 = data1
            value2, line2 = data2
            if value1 != value2:
                file_path, func_name, var_name = key
                changed_values.append({
                    "file": file_path,
                    "function": func_name,
                    "variable": var_name,
                    "old_value": value1,
                    "new_value": value2,
                    "old_line": line1,
                    "new_line": line2,
                })

    if not changed_values:
        print("\nNo changed constant values found between the two versions.")
    else:
        # Sort results for consistent output
        changed_values.sort(key=lambda x: (x['file'], x['function'], x['variable']))

        # Save to CSV
        print(f"\nSaving detailed changes to {csv_file_path}...")
        try:
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'File', 'Function', 'Variable', 'Old Value', 'New Value',
                    'Old Location', 'New Location'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for change in changed_values:
                    file_path = change['file']
                    path1 = os.path.join(prefix1, file_path)
                    path2 = os.path.join(prefix2, file_path)

                    writer.writerow({
                        'File': file_path,
                        'Function': change['function'],
                        'Variable': change['variable'],
                        'Old Value': change['old_value'],
                        'New Value': change['new_value'],
                        'Old Location': f"{path1}:{change['old_line']}",
                        'New Location': f"{path2}:{change['new_line']}"
                    })
            print(f"Successfully saved {len(changed_values)} changes to {csv_file_path}.")
        except IOError as e:
            print(f"Error writing to CSV file: {e}", file=sys.stderr)

        print(f"\nFound {len(changed_values)} instances of changed constant values:")
        for change in changed_values:
            file_path = change['file']
            # Create full paths with version prefixes
            path1 = os.path.join(prefix1, file_path)
            path2 = os.path.join(prefix2, file_path)

            print(f"- File:     {path1}:{change['old_line']} {path2}:{change['new_line']}")
            print(f"  Function: {change['function']}")
            print(f"  Variable: {change['variable']}")
            print(f"  Value:    {change['old_value']} -> {change['new_value']}\n")

    print("---")
    print("Note: This comparison is based on (file_path, function_name, variable_name) as a unique key.")
    print("If a variable is assigned multiple times in the same file, only the last assignment in the log is considered.")


if __name__ == "__main__":
    main()
