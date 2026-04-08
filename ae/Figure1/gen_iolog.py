#!/usr/bin/env python3
import argparse, random, sys

def main():
    p = argparse.ArgumentParser(description="Generate fio iolog of randomized 4K IOs per region.")
    p.add_argument("--outfile", default="iolog_write.txt", help="Output iolog filename")
    p.add_argument("--dev", dest="dev_name", default="/dev/sdb", help="Device token/path in iolog")
    p.add_argument("--op", dest="task_type", default="write", choices=["read","write","mix"], help="I/O op")
    p.add_argument("--read-ratio", type=float, default=0.5, help="Read ratio for mix mode (0.0-1.0, default 0.5)")
    p.add_argument("--regions", type=int, default=256, help="# of regions")
    p.add_argument("--ios-per-region", type=int, default=128, help="# of IOs per region")
    p.add_argument("--bs", type=int, default=4096, help="IO size in bytes (default 4096, must align to device LBS)")
    p.add_argument("--stride", type=int, default=0, help="Byte spacing between adjacent sorted IOs (default: 0)")
    p.add_argument("--start-offset", type=int, default=0, help="Starting byte offset")
    p.add_argument("--region-gap", type=int, default=0, help="Extra byte gap between regions (default: 0, regions are contiguous)")
    p.add_argument("--repeat", type=int, default=5, help="Repeat the entire pattern N times")
    p.add_argument("--shuffle", default="random", choices=["random","adversarial"],
                   help="Shuffle mode: random (default) or adversarial (minimize merging in small batches)")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    args = p.parse_args()

    # Validate read_ratio
    if args.task_type == "mix" and (args.read_ratio < 0.0 or args.read_ratio > 1.0):
        print("Error: read_ratio must be between 0.0 and 1.0", file=sys.stderr)
        return 1

    random.seed(args.seed)

    stride = args.stride if args.stride else args.bs
    # region size = ios_per_region * stride
    region_sz = args.ios_per_region * stride
    with open(args.outfile, "w") as f:
        f.write("fio version 2 iolog\n")
        f.write(f"{args.dev_name} add\n")
        f.write(f"{args.dev_name} open\n")

        for _rep in range(args.repeat):
            base0 = args.start_offset
            for r in range(args.regions):
                base = base0 + r * (region_sz + args.region_gap)
                # Generate all 4K-aligned offsets within this region
                offs = [base + i*stride for i in range(args.ios_per_region)]
                if args.shuffle == "adversarial":
                    # Interleave: pick every Nth element so that consecutive
                    # groups of ~32 IOs have no adjacent offsets → zero merging
                    n = args.ios_per_region
                    k = n // 32 if n >= 32 else 1  # stride factor
                    offs_sorted = sorted(offs)
                    offs = [offs_sorted[(i * k) % n + (i * k) // n] for i in range(n)]
                else:
                    random.shuffle(offs)
                
                if args.task_type == "mix":
                    for off in offs:
                        op = "read" if random.random() < args.read_ratio else "write"
                        f.write(f"{args.dev_name} {op} {off} {args.bs}\n")
                else:
                    for off in offs:
                        f.write(f"{args.dev_name} {args.task_type} {off} {args.bs}\n")

        f.write(f"{args.dev_name} close\n")

if __name__ == "__main__":
    sys.exit(main())
