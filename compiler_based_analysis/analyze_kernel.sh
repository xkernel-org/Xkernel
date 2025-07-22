#!/bin/bash

KERNEL_DIR=${1:-"kernel_build_dir/linux-$VERSION"}
OUTPUT_DIR=${2:-"log_dir/log-$VERSION"}
N_JOBS=${N_JOBS:-$(nproc)}

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_VERSION=$( cd $THIS_DIR; git log --pretty='format:%h "%s"' -n 1 )

print_time_diff() {
    T1=$1
    T2=$2

    DIFF=$((T2 - T1))

    HOURS=$((DIFF / 3600))
    MINUTES=$(((DIFF % 3600) / 60))
    SECONDS=$((DIFF % 60))

    printf "%02d:%02d:%02d\n" $HOURS $MINUTES $SECONDS
}

T1=$( date +%s )
date > start_time.txt

if [[ ! -d $KERNEL_DIR ]]; then
    echo "Kernel directory $KERNEL_DIR does not exist"
    exit 1
fi

if [[ ! -f $KERNEL_DIR/compile_commands.json ]]; then
    echo "compile_commands.json not found in $KERNEL_DIR"
    exit 1
fi

if [[ ! -f $KERNEL_DIR/compiled_c_files.txt ]]; then
    echo "compiled_c_files.txt not found in $KERNEL_DIR"
    exit 1
fi

if [[ -d $OUTPUT_DIR ]]; then
    echo "Output directory $OUTPUT_DIR already exists"
    exit 1
fi

mkdir -p $OUTPUT_DIR

analyze_file() {
    FILE="$1"

    echo "Processing $FILE"
    mkdir -p "$OUTPUT_DIR/$(dirname "$FILE")"
    FILE_LOG="$OUTPUT_DIR/$(dirname "$FILE")/$(basename "$FILE").txt"

    tool/constant_analysis --mode=int-literal -p "$KERNEL_DIR" \
        "$KERNEL_DIR/$FILE" 2>&1 | \
        sed "s|$REAL_KERNEL_PATH/||g" | \
        tee "$FILE_LOG" >/dev/null
}

export -f analyze_file
export KERNEL_DIR
export OUTPUT_DIR
export REAL_KERNEL_PATH=$(realpath "$KERNEL_DIR")

echo "Running analysis in parallel with $N_JOBS jobs"

cat "$KERNEL_DIR/compiled_c_files.txt" | xargs -P"$N_JOBS" -I{} bash -c 'analyze_file "{}"'

cd $OUTPUT_DIR
find . -type f -name "*.txt" -exec cat {} + > all.txt.1

T2=$( date +%s )

echo "----------------------------------------"
echo "Duration:              $(print_time_diff $T1 $T2)"
echo "Script & tool version: $SCRIPT_VERSION"
echo "----------------------------------------"
clang --version
echo "----------------------------------------"
