#!/bin/bash

KERNEL_DIR=$(realpath "$1" | sed 's/\/$//')
PATCH_FILE=$(realpath "$2" | sed 's/\/$//')

BLUE='\033[34m'
NC='\033[0m'

if [ -z "$SUDO_USER" ]; then
    echo "Error: Please run this script with sudo."
    exit 1
fi

echo -e "${BLUE}Phase 1: Building kernel to generate pre-objs...${NC}"
time make bzImage -C "$KERNEL_DIR" -j$(nproc)

echo -e "${BLUE}Phase 2: Applying patch to the kernel...${NC}"
python patch2sed.py "$PATCH_FILE" "$KERNEL_DIR" --sudo > /dev/null

echo -e "${BLUE}Phase 3: Building kernel to generate post-objs and diffing...${NC}"
./gen-diff.sh "$KERNEL_DIR"

echo -e "${BLUE}Phase 4: Restore the kernel source code...${NC}"
python patch2sed.py "$PATCH_FILE" "$KERNEL_DIR" --sudo -r > /dev/null

echo -e "${BLUE}Phase 5: Diffing object files...${NC}"
python check-diff.py ./tmp/pre_objs/block/blk-throttle.o ./tmp/post_objs/block/blk-throttle.o -l 950,960

echo -e "${BLUE}Done.${NC}"
