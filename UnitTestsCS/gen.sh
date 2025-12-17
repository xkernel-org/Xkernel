#!/bin/bash
# Script to read cmd.sh and extract step 11 output to res_*.txt for each test
# Format: one command per line, automatically numbered

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CMD_FILE="cmd.sh"

if [ ! -f "$CMD_FILE" ]; then
    echo "Error: $CMD_FILE not found!"
    exit 1
fi

test_num=0

# Read cmd.sh line by line
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Increment test number
    ((test_num++))
    res_file="res_${test_num}.txt"
    
    echo "Running TEST $test_num -> $res_file..."
    echo "Command: $line"
    
    # Execute the command and capture all output
    output=$(eval "$line" 2>&1)
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo "Error: Test $test_num failed with exit code $exit_code" > "$res_file"
        echo "Command: $line" >> "$res_file"
        echo "Full output:" >> "$res_file"
        echo "$output" >> "$res_file"
        continue
    fi
    
    # Extract step 11 output
    # Step 11 starts with "11. Extracting Basic Blocks for changed instructions..."
    # and continues until step 12 starts or end of output
    # Remove ANSI color codes for cleaner output
    step11_output=$(echo "$output" | sed 's/\x1b\[[0-9;]*m//g' | awk '
        /11\. Extracting Basic Blocks for changed instructions\.\.\./ {
            in_step11 = 1
            print
            next
        }
        in_step11 {
            # Stop at step 12 or script finished message
            if (/^12\./ || /^Script finished successfully\./ || /^All disassembly files saved to/) {
                in_step11 = 0
                exit
            }
            print
        }
    ')
    
    # Write step 11 output to result file
    if [ -n "$step11_output" ]; then
        echo "$step11_output" > "$res_file"
        echo "  -> Step 11 output written to $res_file"
    else
        echo "  -> Warning: No step 11 output found, creating empty file"
        echo "# No step 11 output found" > "$res_file"
    fi
done < "$CMD_FILE"

echo "Done processing all test cases."

