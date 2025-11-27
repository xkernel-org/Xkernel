#!/usr/bin/env python3

import sys
import statistics

def parse_time(time_str):
    time_str = time_str.strip()
    parts = time_str.split(':')

    if len(parts) == 3:
        hours, minutes, seconds = (float(p) for p in parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes, seconds = (float(p) for p in parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")

def format_time(total_seconds):
    total_seconds = round(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def main():
    times_in_seconds = []

    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                seconds = parse_time(line)
                times_in_seconds.append(seconds)
            except (ValueError, IndexError) as e:
                print(f"Error parsing line '{line}': {e}", file=sys.stderr)
                continue

    if not times_in_seconds:
        print("No valid time entries found.", file=sys.stderr)
        sys.exit(1)

    avg_seconds = statistics.mean(times_in_seconds)
    median_seconds = statistics.median(times_in_seconds)

    print(f"Average time: {format_time(avg_seconds)}")
    print(f"Median time: {format_time(median_seconds)}")

if __name__ == "__main__":
    main()
