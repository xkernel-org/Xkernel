#!/usr/bin/env python3
import argparse, random, sys

def main():
    p = argparse.ArgumentParser(description="Generate fio iolog v3 of randomized 4K IOs per region.")
    p.add_argument("--outfile", default="seq_v3.txt", help="Output iolog filename")
    p.add_argument("--dev", dest="dev_name", default="/dev/target", help="Device token/path in iolog")
    p.add_argument("--op", dest="task_type", default="read", choices=["read","write","mix"], help="I/O op")
    p.add_argument("--read-ratio", type=float, default=0.5, help="Read ratio for mix mode (0.0-1.0, default 0.5)")
    p.add_argument("--regions", type=int, default=64, help="# of regions")
    p.add_argument("--ios-per-region", type=int, default=128, help="# of IOs per region")
    p.add_argument("--bs", type=int, default=4096, help="IO size in bytes (default 4096, must align to device LBS)")
    p.add_argument("--start-offset", type=int, default=0, help="Starting byte offset")
    p.add_argument("--repeat", type=int, default=1, help="Repeat the entire pattern N times")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    args = p.parse_args()

    # Validate read_ratio
    if args.task_type == "mix" and (args.read_ratio < 0.0 or args.read_ratio > 1.0):
        print("Error: read_ratio must be between 0.0 and 1.0", file=sys.stderr)
        return 1

    random.seed(args.seed)

    # region size = ios_per_region * bs
    region_sz = args.ios_per_region * args.bs
    ts = 0
    with open(args.outfile, "w") as f:
        f.write("fio version 3 iolog\n")
        f.write(f"{ts} {args.dev_name} add\n"); ts += 1
        f.write(f"{ts} {args.dev_name} open\n"); ts += 1

        for _rep in range(args.repeat):
            base0 = args.start_offset
            for r in range(args.regions):
                base = base0 + r * region_sz
                # Generate all 4K-aligned offsets within this region
                offs = [base + i*args.bs for i in range(args.ios_per_region)]
                random.shuffle(offs)  # random order *within* region
                
                if args.task_type == "mix":
                    # For mix mode, determine read/write operations for each IO
                    for off in offs:
                        op = "read" if random.random() < args.read_ratio else "write"
                        f.write(f"{ts} {args.dev_name} {op} {off} {args.bs}\n")
                        ts += 1
                else:
                    # For read/write mode, use the specified operation
                    for off in offs:
                        f.write(f"{ts} {args.dev_name} {args.task_type} {off} {args.bs}\n")
                        ts += 1
            # next repeat continues immediately after previous (no gaps)

        f.write(f"{ts} {args.dev_name} close\n")

if __name__ == "__main__":
    sys.exit(main())
