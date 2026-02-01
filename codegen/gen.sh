#!/bin/bash
# Script to read testcases.sh and extract Basic Block output
# Format: every two lines form a group (original value -> modified value pairs)
# Output: *_bb_v1.txt (step 11 from first command), *_bb_v2.txt (step 11b from first command), *_bb_v3.txt (step 11b from second command)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CMD_FILE="testcases.sh"

if [ ! -f "$CMD_FILE" ]; then
    echo "Error: $CMD_FILE not found!"
    exit 1
fi

test_num=0
cmd1=""
cmd2=""
first_line=true
accumulating_cmd=""

# Read cmd_v2.sh line by line
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Skip first line if it contains V1,V2,V3 (format: number,number,number)
    if [ "$first_line" = true ]; then
        first_line=false
        # Check if line matches pattern: digits,digits,digits
        if [[ "$line" =~ ^[[:space:]]*[0-9]+[[:space:]]*,[[:space:]]*[0-9]+[[:space:]]*,[[:space:]]*[0-9]+[[:space:]]*$ ]]; then
            continue
        fi
    fi
    
    # Check if line ends with backslash (command continuation)
    if [[ "$line" =~ \\[[:space:]]*$ ]]; then
        # Remove trailing backslash and whitespace, add to accumulating command
        if [ -z "$accumulating_cmd" ]; then
            accumulating_cmd="${line%\\}"
        else
            accumulating_cmd="${accumulating_cmd} ${line%\\}"
        fi
        continue
    fi
    
    # If we were accumulating a command, complete it
    if [ -n "$accumulating_cmd" ]; then
        line="${accumulating_cmd} ${line}"
        accumulating_cmd=""
    fi
    
    # Store first command
    if [ -z "$cmd1" ]; then
        cmd1="$line"
        continue
    fi
    
    # Store second command
    if [ -z "$cmd2" ]; then
        cmd2="$line"
    fi
    
    # Process the group when we have both commands
    if [ -n "$cmd1" ] && [ -n "$cmd2" ]; then
        ((test_num++))
        
        v1_file="${test_num}_bb_v1.txt"
        v2_file="${test_num}_bb_v2.txt"
        v3_file="${test_num}_bb_v3.txt"
        
        echo "Processing TEST GROUP $test_num..."
        echo "  Command 1: $cmd1"
        echo "  Command 2: $cmd2"
        
        # Execute first command and capture all output
        echo "  -> Executing command 1..."
        # Use temporary file to capture output to avoid buffering issues
        # Change to parent directory where check_assembly_diff.py is located
        tmp_output1=$(mktemp)
        (cd "$SCRIPT_DIR/.." && PYTHONUNBUFFERED=1 bash -c "$cmd1") > "$tmp_output1" 2>&1
        exit_code1=$?
        output1=$(cat "$tmp_output1")
        rm -f "$tmp_output1"
        
        if [ $exit_code1 -ne 0 ]; then
            echo "  -> Error: Command 1 failed with exit code $exit_code1"
            echo "# Command 1 failed: $cmd1" > "$v1_file"
            echo "# Command 1 failed: $cmd1" > "$v2_file"
            echo "# Command 1 failed: $cmd1" > "$v3_file"
            cmd1=""
            cmd2=""
            continue
        fi
        
        # Extract step 11 (original) from first command -> v1
        step11_output=$(echo "$output1" | sed 's/\x1b\[[0-9;]*m//g' | awk '
            BEGIN { in_step11 = 0 }
            /^11\. Extracting Basic Blocks for changed instructions\.\.\./ {
                in_step11 = 1
                # Skip the header line
                next
            }
            in_step11 == 1 {
                # Stop at step 11b or step 12 or script finished message
                if (/^11b\./ || /^12\./ || /^Script finished successfully\./ || /^All disassembly files saved to/) {
                    in_step11 = 0
                    exit
                }
                # Skip "Instruction at..." lines
                if (/^Instruction at 0x/ && /found at line/) {
                    next
                }
                print
            }
        ')
        
        if [ -n "$step11_output" ]; then
            echo "$step11_output" > "$v1_file"
            echo "    -> Step 11 (original) written to $v1_file"
        else
            echo "    -> Warning: No step 11 output found for v1"
            echo "# No step 11 output found" > "$v1_file"
        fi
        
        # Extract step 11b (recompiled) from first command -> v2
        step11b_output=$(echo "$output1" | sed 's/\x1b\[[0-9;]*m//g' | awk '
            BEGIN { in_step11b = 0 }
            /^11b\./ {
                in_step11b = 1
                # Skip the header line
                next
            }
            in_step11b == 1 {
                # Stop at step 12 or script finished message
                if (/^12\./ || /^Script finished successfully\./ || /^All disassembly files saved to/) {
                    in_step11b = 0
                    exit
                }
                # Skip "Instruction at..." lines
                if (/^Instruction at 0x/ && /found at line/) {
                    next
                }
                print
            }
        ')
        
        if [ -n "$step11b_output" ]; then
            echo "$step11b_output" > "$v2_file"
            echo "    -> Step 11b (recompiled) from command 1 written to $v2_file"
        else
            echo "    -> Warning: No step 11b output found for v2"
            echo "# No step 11b output found" > "$v2_file"
        fi
        
        # Execute second command and capture all output
        echo "  -> Executing command 2..."
        # Use temporary file to capture output to avoid buffering issues
        # Change to parent directory where check_assembly_diff.py is located
        tmp_output2=$(mktemp)
        (cd "$SCRIPT_DIR/.." && PYTHONUNBUFFERED=1 bash -c "$cmd2") > "$tmp_output2" 2>&1
        exit_code2=$?
        output2=$(cat "$tmp_output2")
        rm -f "$tmp_output2"
        
        if [ $exit_code2 -ne 0 ]; then
            echo "  -> Error: Command 2 failed with exit code $exit_code2"
            echo "# Command 2 failed: $cmd2" > "$v3_file"
            cmd1=""
            cmd2=""
            continue
        fi
        
        # Extract step 11b (recompiled) from second command -> v3
        step11b_output2=$(echo "$output2" | sed 's/\x1b\[[0-9;]*m//g' | awk '
            BEGIN { in_step11b = 0 }
            /^11b\./ {
                in_step11b = 1
                # Skip the header line
                next
            }
            in_step11b == 1 {
                # Stop at step 12 or script finished message
                if (/^12\./ || /^Script finished successfully\./ || /^All disassembly files saved to/) {
                    in_step11b = 0
                    exit
                }
                # Skip "Instruction at..." lines
                if (/^Instruction at 0x/ && /found at line/) {
                    next
                }
                print
            }
        ')
        
        if [ -n "$step11b_output2" ]; then
            echo "$step11b_output2" > "$v3_file"
            echo "    -> Step 11b (recompiled) from command 2 written to $v3_file"
        else
            echo "    -> Warning: No step 11b output found for v3"
            echo "# No step 11b output found" > "$v3_file"
        fi
        
        # Reset for next group
        cmd1=""
        cmd2=""
        first_line=true  # Reset to skip V,V',V'' line of next group
        echo ""
    fi
done < "$CMD_FILE"

# Handle case where there's an odd number of commands (one command left)
if [ -n "$cmd1" ] && [ -z "$cmd2" ]; then
    echo "Warning: Found an unpaired command at the end: $cmd1"
    echo "Skipping this command (need pairs of commands)"
fi

echo "Done processing all test groups."

