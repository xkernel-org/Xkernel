#!/bin/bash

# Script to extract parameters from dataset/ir-occurrence.sh
# and save them with kernel-results/MACRO/IDX.input.txt structure

INPUT_FILE="dataset/ir-occurrence.sh"
OUTPUT_DIR="kernel-results"

mkdir -p "$OUTPUT_DIR"

current_macro=""
current_idx=0
in_case=false
case_data=""

while IFS= read -r line; do
    if [[ "$line" =~ ^###[[:space:]]+[0-9]+\.[[:space:]]+([A-Z_]+) ]]; then

        if [ -n "$current_macro" ] && [ -n "$case_data" ]; then
            macro_dir="$OUTPUT_DIR/$current_macro"
            mkdir -p "$macro_dir"
            echo "$case_data" > "$macro_dir/$current_idx.input.txt"
            echo "Saved: $macro_dir/$current_idx.input.txt"
        fi

        current_macro="${BASH_REMATCH[1]}"
        current_idx=0
        in_case=false
        case_data=""
        continue
    fi

    if [[ "$line" =~ ^SOURCE_FILE= ]] || [[ "$line" =~ ^#[[:space:]]*SOURCE_FILE= ]]; then
        if [ -n "$current_macro" ] && [ -n "$case_data" ]; then
            macro_dir="$OUTPUT_DIR/$current_macro"
            mkdir -p "$macro_dir"
            echo "$case_data" > "$macro_dir/$current_idx.input.txt"
            echo "Saved: $macro_dir/$current_idx.input.txt"
        fi

        ((current_idx++))
        in_case=true
        case_data=""

        cleaned_line=$(echo "$line" | sed 's/^#[[:space:]]*//')
        case_data="$cleaned_line"
        continue
    fi

    if [ "$in_case" = true ]; then
        if [[ "$line" =~ ^(FUNCTION_NAME|SOURCE_OP|CONSTANT_VALUE|OCCURENCE)= ]] || \
           [[ "$line" =~ ^#[[:space:]]*(FUNCTION_NAME|SOURCE_OP|CONSTANT_VALUE|OCCURENCE)= ]]; then
            cleaned_line=$(echo "$line" | sed 's/^#[[:space:]]*//')
            case_data="$case_data"$'\n'"$cleaned_line"
        elif [[ "$line" =~ ^[[:space:]]*$ ]]; then
            continue
        else
            true
            # if [[ "$line" =~ ^#[[:space:]]*#[[:space:]]* ]]; then
            #     cleaned_line=$(echo "$line" | sed 's/^#[[:space:]]*#[[:space:]]*//')
            #     case_data="$case_data"$'\n'"# $cleaned_line"
            # fi
        fi
    fi
done < "$INPUT_FILE"

if [ -n "$current_macro" ] && [ -n "$case_data" ]; then
    macro_dir="$OUTPUT_DIR/$current_macro"
    mkdir -p "$macro_dir"
    echo "$case_data" > "$macro_dir/$current_idx.input.txt"
    echo "Saved: $macro_dir/$current_idx.input.txt"
fi

echo ""
echo "Extraction complete! Results saved in $OUTPUT_DIR/"
