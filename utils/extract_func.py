#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) != 2:
        exit(1)

    path = '../linux-wllvm-defconfig//vmlinux.ll'
    func_name = sys.argv[1]

    # Regex to detect the target function definition line.
    # Matches lines like:
    #   define internal void @amt_event_work(ptr noundef %0) #0 align 16 !dbg !...
    pattern = re.compile(rf'^\s*define\b.*@{re.escape(func_name)}\s*\(')

    in_func = False

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not in_func:
                    # Look for the function definition line
                    if pattern.search(line):
                        in_func = True
                        sys.stdout.write(line)
                else:
                    # Already inside the function; print lines until closing brace
                    sys.stdout.write(line)
                    # LLVM IR pretty consistently ends functions with a line "}"
                    if line.strip() == "}":
                        break
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    if not in_func:
        print(f"Error: function @{func_name} not found in {path}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
