import sys
import json
from pathlib import Path

SNAPSHOT_DIR = Path("/tmp/numa_stats")
SNAPSHOT_1_FILE = SNAPSHOT_DIR / "snapshot1.json"
SNAPSHOT_2_FILE = SNAPSHOT_DIR / "snapshot2.json"

NUMA_FIELDS = [
    "numa_hit",
    "numa_miss",
    "numa_foreign",
    "numa_interleave",
    "numa_local",
    "numa_other",
    "numa_pte_updates",
    "numa_huge_pte_updates",
    "numa_hint_faults",
    "numa_hint_faults_local",
    "numa_pages_migrated",
]

def get_stats():
    """Reads /proc/vmstat and returns a dictionary of NUMA stats."""
    stats = {}
    try:
        with open("/proc/vmstat", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and parts[0] in NUMA_FIELDS:
                    stats[parts[0]] = int(parts[1])
    except FileNotFoundError:
        print("Error: /proc/vmstat not found. Is this a Linux system?", file=sys.stderr)
        sys.exit(1)
    return stats

def save_snapshot(stats, filepath):
    """Saves the collected stats to a file in JSON format."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(stats, f, indent=2)

def load_snapshot(filepath):
    """Loads stats from a JSON file."""
    if not filepath.exists():
        print(f"Error: Snapshot file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r") as f:
        return json.load(f)

def print_diff(s1, s2):
    """Prints a formatted report comparing two snapshots and their delta."""
    print(f"{'Metric':<25} {'Snapshot 1':>18} {'Snapshot 2':>18} {'Delta':>18}")
    print("-" * 79)
    for key in NUMA_FIELDS:
        val1 = s1.get(key)
        val2 = s2.get(key)
        delta = val2 - val1
        print(f"{key:<25} {val1:>18,} {val2:>18,} {delta:>18,}")

def usage():
    print("Usage: python numa_stat.py save1|save2|diff", file=sys.stderr)
    sys.exit(1)

def main():
    args = sys.argv

    if len(args) != 2:
        usage()

    if args[1] == "save1":
        stats = get_stats()
        save_snapshot(stats, SNAPSHOT_1_FILE)
    elif args[1] == "save2":
        stats = get_stats()
        save_snapshot(stats, SNAPSHOT_2_FILE)
    elif args[1] == "diff":
        s1_data = load_snapshot(SNAPSHOT_1_FILE)
        s2_data = load_snapshot(SNAPSHOT_2_FILE)
        print_diff(s1_data, s2_data)
    else:
        usage()

if __name__ == "__main__":
    main()
