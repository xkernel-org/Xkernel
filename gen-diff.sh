#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Error: Please provide kernel source directory as an argument."
    echo "Usage: $0 <kernel_source_directory>"
    exit 1
fi

KERNEL_DIR=$(realpath "$1" | sed 's/\/$//')

if [ ! -d "$KERNEL_DIR" ]; then
    echo "Error: Directory $KERNEL_DIR does not exist."
    exit 1
fi

mkdir -p ./tmp/{pre_objs,post_objs}

echo "Fast backing up original .o files (excluding drivers/)..."

find "$KERNEL_DIR" -name "*.o" -type f \
    -not -path "$KERNEL_DIR/arch/*" \
    -not -path "$KERNEL_DIR/init/*" \
    -not -path "$KERNEL_DIR/drivers/*" \
    -not -name ".tmp_vmlinux*" \
    -not -name "vmlinux.o" \
    -printf "%T@ %P\n" > ./tmp/prev_objects.txt

awk '{print $2}' ./tmp/prev_objects.txt > ./tmp/prev_files.txt

time rsync -a --files-from=./tmp/prev_files.txt \
    --exclude='drivers/***' \
    "$KERNEL_DIR/" ./tmp/pre_objs/

echo "Starting kernel compilation... (time will be recorded)"
time make bzImage -C "$KERNEL_DIR" "${@:2}" -j$(nproc)

find "$KERNEL_DIR" -name "*.o" -type f -printf "%T@ %P\n" > ./tmp/curr_objects.txt

echo "Finding changed object files with filters..."
comm -13 <(sort ./tmp/prev_objects.txt) <(sort ./tmp/curr_objects.txt) | awk '{print $2}' | \
    grep -v '^\.tmp_vmlinux' | \
    grep -v '^arch/' | \
    grep -v '^init/' | \
    grep -v '^drivers/' | \
    grep -v '^vmlinux\.o$' > ./tmp/new_objects.txt

echo "Copying modified versions of changed files..."
while read -r rel_path; do
    obj_file="$KERNEL_DIR/$rel_path"
    if [ -f "$obj_file" ]; then
        dest_modified="./tmp/post_objs/$rel_path"
        mkdir -p "$(dirname "$dest_modified")"
        cp "$obj_file" "$dest_modified"
        echo "Copied modified: $rel_path"
    fi
done < ./tmp/new_objects.txt

echo "Cleaning pre_objs to only keep modified files..."

> ./tmp/keep_files.txt

while read -r rel_path; do
    echo "$rel_path" >> ./tmp/keep_files.txt
done < ./tmp/new_objects.txt

find ./tmp/pre_objs -type f -name "*.o" | while read -r orig_file; do
    rel_path="${orig_file#./tmp/pre_objs/}"
    
    if ! grep -qxF "$rel_path" ./tmp/keep_files.txt; then
        rm -f "$orig_file"
    fi
done

find ./tmp/pre_objs -type d -empty -delete

rm ./tmp/prev_objects.txt ./tmp/curr_objects.txt ./tmp/new_objects.txt ./tmp/prev_files.txt ./tmp/keep_files.txt

echo -e "\nOperation completed."
echo "Modified files saved in: ./tmp/post_objs"
echo "Original versions of modified files saved in: ./tmp/pre_objs"
