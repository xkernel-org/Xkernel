#!/usr/bin/env python3
import argparse, random, sys

def main():
    p = argparse.ArgumentParser(description="Generate fio iolog v3 of randomized 4K IOs per region.")
    p.add_argument("--outfile", default="seq_v3.txt", help="Output iolog filename")
    p.add_argument("--dev", dest="dev_name", default="/dev/target", help="Device token/path in iolog")
    p.add_argument("--op", dest="task_type", default="read", choices=["read","write"], help="I/O op")
    p.add_argument("--regions", type=int, default=64, help="# of regions")
    p.add_argument("--ios-per-region", type=int, default=128, help="# of IOs per region")
    p.add_argument("--bs", type=int, default=4096, help="IO size in bytes (default 4096, must align to device LBS)")
    p.add_argument("--start-offset", type=int, default=0, help="Starting byte offset")
    p.add_argument("--repeat", type=int, default=1, help="Repeat the entire pattern N times")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    args = p.parse_args()

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
                for off in offs:
                    f.write(f"{ts} {args.dev_name} {args.task_type} {off} {args.bs}\n")
                    ts += 1
            # next repeat continues immediately after previous (no gaps)

        f.write(f"{ts} {args.dev_name} close\n")

if __name__ == "__main__":
    sys.exit(main())
