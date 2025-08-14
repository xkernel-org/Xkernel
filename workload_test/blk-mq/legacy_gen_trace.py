import random
import argparse

# --- Constants ---
# Each I/O request size in bytes
BLOCK_SIZE = 4096  # 4KB
# Number of 4K blocks in one large sequential region
BLOCKS_PER_REGION = 128
# Total size of one region (e.g., 128 * 4KB = 512KB)
REGION_SIZE = BLOCK_SIZE * BLOCKS_PER_REGION

def generate_iolog(num_regions, task_type, output_file):
    """
    Generates a fio iolog file.

    The log contains a series of regions. Within each region, the 4K block
    offsets are accessed randomly. The regions themselves are accessed sequentially.

    Args:
        num_regions (int): The number of sequential regions to generate.
        task_type (str): The I/O operation type ('read', 'write', etc.).
        output_file (str): The path to the output log file.
    """
    print(f"Generating log for {num_regions} region(s)...")
    print(f"  - Region size: {REGION_SIZE // 1024}KB")
    print(f"  - I/O size: {BLOCK_SIZE // 1024}KB")
    print(f"  - Total I/Os: {num_regions * BLOCKS_PER_REGION}")
    print(f"  - Total data: {(num_regions * REGION_SIZE) / (1024**2):.2f} MB")

    with open(output_file, 'w') as f:
        for i in range(num_regions):
            # Calculate the starting offset for the current sequential region
            region_start_offset = i * REGION_SIZE

            # Create a list of all 4K offsets within this region
            offsets_in_region = [
                region_start_offset + (j * BLOCK_SIZE) for j in range(BLOCKS_PER_REGION)
            ]

            # Shuffle the offsets to create a random access pattern within the region
            random.shuffle(offsets_in_region)

            # Write the shuffled operations to the log file
            # Format: rw, offset, length
            for offset in offsets_in_region:
                f.write(f"{task_type}, {offset}, {BLOCK_SIZE}\n")

    print(f"\n✅ Successfully created log file: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a fio iolog for semi-sequential workloads."
    )
    parser.add_argument(
        "--regions",
        type=int,
        default=100,
        help="Number of 512KB regions to generate in the workload.",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="read",
        choices=["read", "write", "trim"],
        help="The I/O task type (e.g., read, write).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="seq.txt",
        help="Name of the output log file.",
    )
    args = parser.parse_args()

    generate_iolog(args.regions, args.task, args.output)