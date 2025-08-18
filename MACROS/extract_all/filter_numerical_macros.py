import os
import csv
import re
import argparse

# --- Script Setup ---
parser = argparse.ArgumentParser(
    description='Filter numeric macros and re-classify them by subsystem.'
)
parser.add_argument(
    '--input_dir', 
    type=str, 
    default='classified_constants', 
    help='Directory containing the classified *_macro.csv files.'
)
parser.add_argument(
    '--output_dir', 
    type=str, 
    default='filtered_numerical_classified_macros', 
    help='Directory to save the new filtered and classified CSV files.'
)
args = parser.parse_args()

INPUT_DIR = args.input_dir
OUTPUT_DIR = args.output_dir

def contains_number(value_string):
    """
    Checks if a string contains at least one digit using regex.
    """
    if not value_string:
        return False
    return bool(re.search(r'\d', value_string))

def filter_and_reclassify_macros():
    """
    Scans macro CSV files, filters for those containing numeric values in their 
    'Name', 'Value', or 'Description' fields, and saves them to new files, 
    categorized by subsystem.
    """
    # 1. Check if the input directory exists
    if not os.path.isdir(INPUT_DIR):
        print(f"Error: Input directory not found at '{INPUT_DIR}'")
        return

    # 2. Create the output directory if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Input directory: '{INPUT_DIR}'")
    print(f"Output will be saved in: '{OUTPUT_DIR}'")

    output_writers = {}
    open_files = {}
    header = []
    total_found = 0

    try:
        # 3. Walk through the input directory to find relevant files
        print("\nStarting processing...")
        for filename in sorted(os.listdir(INPUT_DIR)):
            if not filename.endswith("_macro.csv"):
                continue

            file_path = os.path.join(INPUT_DIR, filename)
            print(f"  -> Scanning {filename}...")
            
            with open(file_path, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                if not header and reader.fieldnames:
                    header = reader.fieldnames
                
                # 4. Check each row in the current file
                for row in reader:
                    # --- 主要修改区域 ---
                    # 获取所有可能包含数字的栏位内容
                    macro_name = row.get('Name', '')
                    macro_value = row.get('Value', '')
                    macro_description = row.get('Description', '')
                    
                    # 检查 'Name', 'Value', 或 'Description' 中任意一个是否包含数字
                    if contains_number(macro_name) or contains_number(macro_value) or contains_number(macro_description):
                        total_found += 1
                        subsystem = row.get('Subsystem')
                        
                        # 5. 如果是第一次看到该子系统的数字宏，为其创建新的输出文件
                        if subsystem not in output_writers:
                            output_filename = os.path.join(OUTPUT_DIR, f"filtered_{subsystem}_numeric.csv")
                            outfile = open(output_filename, 'w', newline='', encoding='utf-8')
                            writer = csv.DictWriter(outfile, fieldnames=header)
                            writer.writeheader()
                            output_writers[subsystem] = writer
                            open_files[subsystem] = outfile
                        
                        # 将筛选出的行写入对应的子系统文件
                        output_writers[subsystem].writerow(row)
                        
    finally:
        # 6. 重要：关闭所有已打开的输出文件
        print("\nProcessing complete. Closing all files...")
        for file_handle in open_files.values():
            file_handle.close()

    if total_found > 0:
        print(f"\nFound a total of {total_found} numeric macros.")
        print(f"{len(output_writers)} classified output files were created in '{OUTPUT_DIR}'.")
    else:
        print("\nNo macros matching the criteria were found.")


if __name__ == "__main__":
    filter_and_reclassify_macros()