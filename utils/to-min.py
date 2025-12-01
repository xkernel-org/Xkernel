#!/usr/bin/env python3
import sys

def to_minutes(t):
    t = t.strip().replace(",", ".")
    if not t:
        return None

    parts = t.split(":")

    # h:mm:ss(.fraction)
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 60 + m + s / 60.0

    # m:ss(.fraction)
    if len(parts) == 2:
        m = int(parts[0])
        s = float(parts[1])
        return m + s / 60.0

    raise ValueError(f"Unsupported time format: {t}")

for line in sys.stdin:
    t = line.strip()
    if not t:
        continue
    minutes = to_minutes(t)
    print(f"{minutes:.6f}")

