import csv
import os
import argparse
from collections import defaultdict

# --- Script Setup ---
# Use argparse to make the script flexible.
parser = argparse.ArgumentParser(
    description='Classify constants from a CSV file into separate files based on subsystem and type.'
)
parser.add_argument(
    '--input', 
    type=str, 
    default='constants_table.csv', 
    help='Path to the input CSV file.'
)
parser.add_argument(
    '--output_dir', 
    type=str, 
    default='classified_constants', 
    help='Directory to save the classified CSV files.'
)
args = parser.parse_args()

INPUT_FILE = args.input
OUTPUT_DIR = args.output_dir

def classify_csv():
    """
    Reads the main constants CSV and splits it into smaller CSVs based on
    the subsystem and constant type, only for selected subsystems.
    """
    allowed_subsystems = {'block', 'fs', 'io_uring', 'ipc', 'kernel', 'mm', 'net'}

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at '{INPUT_FILE}'")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output will be saved in the '{OUTPUT_DIR}' directory.")

    output_files = {}
    header = []
    
    try:
        with open(INPUT_FILE, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)

            try:
                header = next(reader)
            except StopIteration:
                print("Warning: The input file is empty.")
                return

            for row in reader:
                subsystem = row[0].strip()
                const_type = row[3].strip()

                # === 过滤非目标子系统 ===
                if subsystem not in allowed_subsystems:
                    continue

                file_key = f"{subsystem}_{const_type}"

                if file_key not in output_files:
                    output_filename = os.path.join(OUTPUT_DIR, f"{file_key}.csv")
                    outfile = open(output_filename, 'w', newline='', encoding='utf-8')
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                    output_files[file_key] = (writer, outfile)

                output_files[file_key][0].writerow(row)

    finally:
        count = 0
        for key, (writer, file_handle) in output_files.items():
            file_handle.close()
            count += 1
        print(f"\nProcessing complete. Successfully created {count} classified files.")



if __name__ == "__main__":
    classify_csv()