#!/usr/bin/env python3
"""
Xkernel Table Manager - Safe query and delete operations for the global Xkernel tables.

Usage:
    python3 xkernel_table_manager.py query [--const-id ID] [--val VAL] [--status STATUS]
    python3 xkernel_table_manager.py delete [--const-id ID] [--val VAL] [--status STATUS] [--all]
    python3 xkernel_table_manager.py list
    python3 xkernel_table_manager.py show
    python3 xkernel_table_manager.py cs [--index N]
    python3 xkernel_table_manager.py ss [--index N]
"""

import os
import sys
import csv
import argparse
import re
from typing import List, Dict, Optional

# ANSI Color codes (subdued palette)
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors (standard, not bright)
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    GRAY = '\033[90m'

    # Background colors
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

# Box drawing characters
class Box:
    TL = '┌'  # Top left
    TR = '┐'  # Top right
    BL = '└'  # Bottom left
    BR = '┘'  # Bottom right
    H = '─'   # Horizontal
    V = '│'   # Vertical
    LT = '├'  # Left T
    RT = '┤'  # Right T
    TT = '┬'  # Top T
    BT = '┴'  # Bottom T
    CROSS = '┼'

def colorize(text, *colors):
    """Apply colors to text."""
    return ''.join(colors) + str(text) + Colors.RESET

def draw_box_top(width):
    """Draw top border of a box."""
    return Box.TL + Box.H * width + Box.TR

def draw_box_bottom(width):
    """Draw bottom border of a box."""
    return Box.BL + Box.H * width + Box.BR

def draw_box_separator(width):
    """Draw separator line inside a box."""
    return Box.LT + Box.H * width + Box.RT

def draw_box_line(content, width):
    """Draw a line inside a box with content."""
    return Box.V + content.ljust(width) + Box.V

SCOPE_TABLE_PATH = "/dev/shm/xkernel/scope_table"
CS_TABLE_PATH = "/dev/shm/xkernel/cs_table"
SS_TABLE_PATH = "/dev/shm/xkernel/ss_table"

SCOPE_TABLE_HEADER = ["ConstID", "Val", "Expression", "CS_Index", "SS_Index", "BPF_File", "Status"]
CS_TABLE_HEADER = ["Index", "CS_Content"]
SS_TABLE_HEADER = ["Index", "SS_Content"]


def read_cs_table() -> Dict[int, str]:
    """Read CS Table and return a dictionary mapping index to content.
    
    Returns:
        Dictionary mapping CS index to CS content
    """
    cs_map = {}
    if os.path.exists(CS_TABLE_PATH):
        with open(CS_TABLE_PATH, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    try:
                        index = int(row[0])
                        content = row[1]
                        cs_map[index] = content
                    except (ValueError, IndexError):
                        continue
    return cs_map


def read_ss_table() -> Dict[int, str]:
    """Read SS Table and return a dictionary mapping index to content.
    
    Returns:
        Dictionary mapping SS index to SS content
    """
    ss_map = {}
    if os.path.exists(SS_TABLE_PATH):
        with open(SS_TABLE_PATH, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    try:
                        index = int(row[0])
                        content = row[1]
                        ss_map[index] = content
                    except (ValueError, IndexError):
                        continue
    return ss_map


def read_scope_table() -> List[Dict[str, str]]:
    """Read all entries from the Scope Table.
    
    Returns:
        List of dictionaries, each representing a row with CS and SS content resolved
    """
    if not os.path.exists(SCOPE_TABLE_PATH):
        return []
    
    # Read CS and SS tables
    cs_map = read_cs_table()
    ss_map = read_ss_table()
    
    entries = []
    with open(SCOPE_TABLE_PATH, 'r', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= len(SCOPE_TABLE_HEADER):
                cs_index = row[3].strip() if len(row) > 3 else ""
                ss_index = row[4].strip() if len(row) > 4 else ""
                
                # Resolve CS and SS content from indices
                cs_content = ""
                ss_content = ""
                if cs_index:
                    try:
                        cs_idx = int(cs_index)
                        cs_content = cs_map.get(cs_idx, f"[CS#{cs_idx} not found]")
                    except ValueError:
                        cs_content = f"[Invalid CS index: {cs_index}]"
                
                if ss_index:
                    try:
                        ss_idx = int(ss_index)
                        ss_content = ss_map.get(ss_idx, f"[SS#{ss_idx} not found]")
                    except ValueError:
                        ss_content = f"[Invalid SS index: {ss_index}]"
                
                entries.append({
                    'ConstID': row[0].strip() if len(row) > 0 else "",
                    'Val': row[1].strip() if len(row) > 1 else "",
                    'Expression': row[2].strip() if len(row) > 2 else "",
                    'CS_Index': cs_index,
                    'SS_Index': ss_index,
                    'CS': cs_content,
                    'SS': ss_content,
                    'BPF_File': row[5].strip() if len(row) > 5 else "",
                    'Status': row[6].strip() if len(row) > 6 else ""
                })
    
    return entries


def write_scope_table(entries: List[Dict[str, str]]):
    """Write entries to the Scope Table.
    
    Args:
        entries: List of dictionaries representing rows (with CS_Index and SS_Index)
    """
    # Create directory if it doesn't exist
    table_dir = os.path.dirname(SCOPE_TABLE_PATH)
    if table_dir and not os.path.exists(table_dir):
        os.makedirs(table_dir, exist_ok=True)
    
    with open(SCOPE_TABLE_PATH, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(SCOPE_TABLE_HEADER)
        for entry in entries:
            writer.writerow([
                entry.get('ConstID', ''),
                entry.get('Val', ''),
                entry.get('Expression', ''),
                entry.get('CS_Index', ''),
                entry.get('SS_Index', ''),
                entry.get('BPF_File', ''),
                entry.get('Status', '')
            ])


def query_entries(const_id: Optional[str] = None, val: Optional[str] = None, 
                  status: Optional[str] = None) -> List[Dict[str, str]]:
    """Query entries from the Scope Table.
    
    Args:
        const_id: Filter by ConstID (optional)
        val: Filter by Val (optional)
        status: Filter by Status (optional)
    
    Returns:
        List of matching entries
    """
    entries = read_scope_table()
    
    filtered = []
    for entry in entries:
        match = True
        if const_id and entry.get('ConstID', '') != const_id:
            match = False
        if val and entry.get('Val', '') != val:
            match = False
        if status and entry.get('Status', '') != status:
            match = False
        
        if match:
            filtered.append(entry)
    
    return filtered


def delete_entries(const_id: Optional[str] = None, val: Optional[str] = None,
                   status: Optional[str] = None, delete_all: bool = False) -> int:
    """Delete entries from the Scope Table.
    
    Args:
        const_id: Delete entries matching ConstID (optional)
        val: Delete entries matching Val (optional)
        status: Delete entries matching Status (optional)
        delete_all: If True, delete all entries (dangerous!)
    
    Returns:
        Number of entries deleted
    """
    if not os.path.exists(SCOPE_TABLE_PATH):
        print(colorize("  Scope Table does not exist.", Colors.YELLOW))
        return 0

    entries = read_scope_table()

    if delete_all:
        if not entries:
            print(colorize("  Scope Table is already empty.", Colors.YELLOW))
            return 0
        count = len(entries)
        write_scope_table([])
        print(colorize(f"  ✓ Deleted all {count} entries from Scope Table.", Colors.GREEN))
        return count
    
    # Filter entries to keep
    to_keep = []
    deleted_count = 0
    
    for entry in entries:
        should_delete = False
        
        if const_id and entry.get('ConstID', '') == const_id:
            should_delete = True
        if val and entry.get('Val', '') == val:
            should_delete = True
        if status and entry.get('Status', '') == status:
            should_delete = True
        
        # If multiple filters, all must match
        if const_id and entry.get('ConstID', '') != const_id:
            should_delete = False
        if val and entry.get('Val', '') != val:
            should_delete = False
        if status and entry.get('Status', '') != status:
            should_delete = False
        
        if should_delete:
            deleted_count += 1
        else:
            to_keep.append(entry)
    
    if deleted_count > 0:
        write_scope_table(to_keep)
        print(colorize(f"  ✓ Deleted {deleted_count} entry/entries from Scope Table.", Colors.GREEN))
    else:
        print(colorize("  No matching entries found to delete.", Colors.YELLOW))

    return deleted_count


def print_scope_table_pretty(entries: List[Dict[str, str]]):
    """Print Scope Table entries in a beautiful formatted table with box drawing."""
    if not entries:
        print(colorize("  No entries found.", Colors.DIM))
        return

    # Define columns with fixed widths for clean alignment
    columns = [
        ('ID', 'ConstID', 4),
        ('Val', 'Val', 6),
        ('Expression', 'Expression', 20),
        ('CS', 'CS_Index', 12),
        ('SS', 'SS_Index', 4),
        ('BPF File', 'BPF_File', 28),
        ('Status', 'Status', 10),
    ]

    # Calculate total width
    total_inner = sum(w for _, _, w in columns) + (len(columns) - 1) * 3  # 3 = " │ "

    # Print top border
    print(colorize(Box.TL + Box.H * (total_inner + 2) + Box.TR, Colors.DIM))

    # Print header row
    header_parts = []
    for label, _, width in columns:
        header_parts.append(colorize(label.center(width), Colors.BOLD))
    header_line = colorize(' ' + Box.V + ' ', Colors.DIM).join(header_parts)
    print(colorize(Box.V + ' ', Colors.DIM) + header_line + colorize(' ' + Box.V, Colors.DIM))

    # Print separator
    sep_parts = [Box.H * w for _, _, w in columns]
    print(colorize(Box.LT + Box.H + (Box.H + Box.TT + Box.H).join(sep_parts) + Box.H + Box.RT, Colors.DIM))

    # Print data rows
    for entry in entries:
        row_parts = []
        for label, key, width in columns:
            val = str(entry.get(key, ''))
            # Truncate if too long
            if len(val) > width:
                val = val[:width-2] + '..'

            # Minimal color coding - only highlight Status
            if key == 'Status':
                if val.lower() == 'active':
                    colored_val = colorize(val.center(width), Colors.GREEN)
                elif val.lower() in ('error', 'failed'):
                    colored_val = colorize(val.center(width), Colors.RED)
                else:
                    colored_val = val.center(width)
            elif key == 'ConstID':
                colored_val = colorize(val.center(width), Colors.BOLD)
            elif key in ('CS_Index', 'SS_Index'):
                colored_val = val.center(width)
            elif key in ('BPF_File', 'Expression'):
                colored_val = val.ljust(width)
            else:
                colored_val = val.center(width)
            row_parts.append(colored_val)

        row_line = colorize(' ' + Box.V + ' ', Colors.DIM).join(row_parts)
        print(colorize(Box.V + ' ', Colors.DIM) + row_line + colorize(' ' + Box.V, Colors.DIM))

    # Print bottom border
    print(colorize(Box.BL + Box.H * (total_inner + 2) + Box.BR, Colors.DIM))


def print_cs_table_pretty(cs_map: Dict[int, str], single_index: int = None):
    """Print CS Table entries in a beautiful format."""
    if not cs_map:
        print(colorize("  No entries found.", Colors.DIM))
        return

    indices_to_show = [single_index] if single_index is not None else sorted(cs_map.keys())

    for index in indices_to_show:
        if index not in cs_map:
            print(colorize(f"  CS index {index} not found.", Colors.RED))
            continue

        content = cs_map[index]
        instructions = [inst.strip() for inst in content.split(';') if inst.strip()]

        # Print CS entry header
        print(colorize(f"  ╭─ ", Colors.DIM) + colorize(f"CS[{index}]", Colors.BOLD) + colorize(" ─" + "─" * 50, Colors.DIM))

        prefix = colorize("  │  ", Colors.DIM)
        if instructions:
            for inst in instructions:
                # Try to parse as assembly: "addr: bytes instruction"
                # e.g., "1f2: c1 e8 03 shr $0x3,%eax"
                asm_match = re.match(r'^([0-9a-fA-F]+):\s+([0-9a-fA-F\s]+)\s+(\S+)\s*(.*)$', inst)
                if asm_match:
                    offset = asm_match.group(1)
                    bytes_hex = asm_match.group(2).strip()
                    opcode = asm_match.group(3)
                    operands = asm_match.group(4)

                    # Minimal coloring
                    line = (f"{prefix}"
                            f"{'0x' + offset:>10} "
                            f"{colorize(bytes_hex, Colors.DIM):24} "
                            f"{opcode:8} "
                            f"{operands}")
                    print(line)
                else:
                    # Try to parse as "func_name,0xaddr,offset_start,offset_end"
                    parts = inst.split(',')
                    if len(parts) >= 4:
                        func_name = parts[0]
                        addr = parts[1]
                        start_off = parts[2]
                        end_off = parts[3]

                        print(f"{prefix}{colorize('func:', Colors.DIM)} {colorize(func_name, Colors.BOLD)}")
                        print(f"{prefix}{colorize('addr:', Colors.DIM)} {addr}  "
                              f"{colorize('range:', Colors.DIM)} [{start_off} -> {end_off}]")
                    else:
                        # Fallback for unrecognized format
                        print(prefix + inst)
        else:
            print(prefix + content)

        print(colorize("  ╰" + "─" * 60, Colors.DIM))


def print_ss_table_pretty(ss_map: Dict[int, str], single_index: int = None):
    """Print SS Table entries in a beautiful format."""
    if not ss_map:
        print(colorize("  No entries found.", Colors.DIM))
        return

    indices_to_show = [single_index] if single_index is not None else sorted(ss_map.keys())

    for index in indices_to_show:
        if index not in ss_map:
            print(colorize(f"  SS index {index} not found.", Colors.RED))
            continue

        content = ss_map[index]

        # Print SS entry header
        print(colorize(f"  ╭─ ", Colors.DIM) + colorize(f"SS[{index}]", Colors.BOLD) + colorize(" ─" + "─" * 50, Colors.DIM))

        # Try to parse the expression: "reg = expression"
        match = re.match(r'^(\w+)\s*=\s*(.+)$', content)
        if match:
            reg = match.group(1)
            expr = match.group(2)
            prefix = colorize("  │  ", Colors.DIM)
            print(f"{prefix}{colorize('target:', Colors.DIM)} {colorize(reg, Colors.BOLD)}")
            print(f"{prefix}{colorize('expr:  ', Colors.DIM)} {expr}")
        else:
            # Truncate if too long
            display = content if len(content) <= 70 else content[:67] + "..."
            print(colorize(f"  │  ", Colors.DIM) + display)

        print(colorize("  ╰" + "─" * 60, Colors.DIM))


def print_section_header(title: str, path: str, count: int, color=Colors.DIM):
    """Print a section header."""
    print()
    print(colorize("  ╔" + "═" * 70 + "╗", Colors.DIM))
    print(colorize("  ║ ", Colors.DIM) + colorize(f" {title}", Colors.BOLD) + " " * (69 - len(title) - 1) + colorize("║", Colors.DIM))
    print(colorize("  ╟" + "─" * 70 + "╢", Colors.DIM))
    print(colorize("  ║ ", Colors.DIM) + colorize(f" Path:   {path}", Colors.DIM) + " " * max(0, 69 - 9 - len(path)) + colorize("║", Colors.DIM))
    print(colorize("  ║ ", Colors.DIM) + colorize(f" Count:  {count}", Colors.DIM) + " " * max(0, 69 - 9 - len(str(count))) + colorize("║", Colors.DIM))
    print(colorize("  ╚" + "═" * 70 + "╝", Colors.DIM))
    print()


def print_entries(entries: List[Dict[str, str]], show_header: bool = True, show_content: bool = True):
    """Print entries in a formatted table (legacy function, calls pretty version)."""
    print_scope_table_pretty(entries)


def main():
    parser = argparse.ArgumentParser(
        description='Manage the global Xkernel tables (Scope, CS, SS)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all tables
  python3 xkernel_table_manager.py list
  
  # Query Scope Table by ConstID
  python3 xkernel_table_manager.py query --const-id CS1
  
  # Query Scope Table by Val
  python3 xkernel_table_manager.py query --val 3
  
  # Query Scope Table by Status
  python3 xkernel_table_manager.py query --status active
  
  # Delete from Scope Table by ConstID
  python3 xkernel_table_manager.py delete --const-id CS1
  
  # Delete from Scope Table by multiple criteria
  python3 xkernel_table_manager.py delete --const-id CS1 --val 3
  
  # Delete all entries from Scope Table (use with caution!)
  python3 xkernel_table_manager.py delete --all
  
  # Show CS Table
  python3 xkernel_table_manager.py cs
  
  # Show specific CS entry
  python3 xkernel_table_manager.py cs --index 1
  
  # Show SS Table
  python3 xkernel_table_manager.py ss
  
  # Show specific SS entry
  python3 xkernel_table_manager.py ss --index 1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query entries from Scope Table')
    query_parser.add_argument('--const-id', help='Filter by ConstID')
    query_parser.add_argument('--val', help='Filter by Val')
    query_parser.add_argument('--status', help='Filter by Status')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete entries from Scope Table')
    delete_parser.add_argument('--const-id', help='Delete entries matching ConstID')
    delete_parser.add_argument('--val', help='Delete entries matching Val')
    delete_parser.add_argument('--status', help='Delete entries matching Status')
    delete_parser.add_argument('--all', action='store_true', 
                               help='Delete all entries (use with caution!)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all tables (Scope, CS, SS)')
    list_parser.add_argument('--indices-only', action='store_true',
                            help='For Scope Table: show only indices instead of full CS/SS content')
    
    # Show command (alias for list)
    show_parser = subparsers.add_parser('show', help='Show all tables (Scope, CS, SS)')
    show_parser.add_argument('--indices-only', action='store_true',
                            help='For Scope Table: show only indices instead of full CS/SS content')
    
    # CS Table command
    cs_parser = subparsers.add_parser('cs', help='Show CS Table')
    cs_parser.add_argument('--index', type=int, help='Show specific CS entry by index')
    
    # SS Table command
    ss_parser = subparsers.add_parser('ss', help='Show SS Table')
    ss_parser.add_argument('--index', type=int, help='Show specific SS entry by index')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'query':
        # Query returns entries with resolved content, but we want to show indices
        # So we need to read raw entries and filter them
        raw_entries = []
        if os.path.exists(SCOPE_TABLE_PATH):
            with open(SCOPE_TABLE_PATH, 'r', newline='') as f:
                reader = csv.reader(f, delimiter='\t')
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= len(SCOPE_TABLE_HEADER):
                        entry = {
                            'ConstID': row[0].strip() if len(row) > 0 else "",
                            'Val': row[1].strip() if len(row) > 1 else "",
                            'Expression': row[2].strip() if len(row) > 2 else "",
                            'CS_Index': row[3].strip() if len(row) > 3 else "",
                            'SS_Index': row[4].strip() if len(row) > 4 else "",
                            'BPF_File': row[5].strip() if len(row) > 5 else "",
                            'Status': row[6].strip() if len(row) > 6 else ""
                        }
                        # Apply filters
                        match = True
                        if args.const_id and entry.get('ConstID', '') != args.const_id:
                            match = False
                        if args.val and entry.get('Val', '') != args.val:
                            match = False
                        if args.status and entry.get('Status', '') != args.status:
                            match = False
                        if match:
                            raw_entries.append(entry)

        # Print filter info
        filters = []
        if args.const_id:
            filters.append(f"ConstID={args.const_id}")
        if args.val:
            filters.append(f"Val={args.val}")
        if args.status:
            filters.append(f"Status={args.status}")
        filter_str = ', '.join(filters) if filters else 'none'

        print()
        print(colorize(f"  Query Results ", Colors.BOLD) + colorize(f"(filters: {filter_str})", Colors.DIM))
        print(f"  Found: {len(raw_entries)} entries")
        print()
        print_scope_table_pretty(raw_entries)
    
    elif args.command == 'delete':
        # Safety check for --all
        if args.all:
            response = input("Are you sure you want to delete ALL entries? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                sys.exit(0)
        
        delete_entries(
            const_id=args.const_id,
            val=args.val,
            status=args.status,
            delete_all=args.all
        )
    
    elif args.command in ['list', 'show']:
        # Print a simple banner
        print()
        print(colorize("  ╔══════════════════════════════════════════════════════════════════════╗", Colors.DIM))
        print(colorize("  ║", Colors.DIM) + colorize("              XKERNEL TABLE MANAGER                                  ", Colors.BOLD) + colorize("║", Colors.DIM))
        print(colorize("  ╚══════════════════════════════════════════════════════════════════════╝", Colors.DIM))

        # Show Scope Table
        raw_entries = []
        if os.path.exists(SCOPE_TABLE_PATH):
            with open(SCOPE_TABLE_PATH, 'r', newline='') as f:
                reader = csv.reader(f, delimiter='\t')
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= len(SCOPE_TABLE_HEADER):
                        raw_entries.append({
                            'ConstID': row[0].strip() if len(row) > 0 else "",
                            'Val': row[1].strip() if len(row) > 1 else "",
                            'Expression': row[2].strip() if len(row) > 2 else "",
                            'CS_Index': row[3].strip() if len(row) > 3 else "",
                            'SS_Index': row[4].strip() if len(row) > 4 else "",
                            'BPF_File': row[5].strip() if len(row) > 5 else "",
                            'Status': row[6].strip() if len(row) > 6 else ""
                        })

        print_section_header("SCOPE TABLE", SCOPE_TABLE_PATH, len(raw_entries), Colors.BLUE)
        print_scope_table_pretty(raw_entries)

        # Show CS Table
        cs_map = read_cs_table()
        print_section_header("CRITICAL SPAN TABLE", CS_TABLE_PATH, len(cs_map), Colors.GREEN)
        print_cs_table_pretty(cs_map)

        # Show SS Table
        ss_map = read_ss_table()
        print_section_header("SYMBOLIC STATE TABLE", SS_TABLE_PATH, len(ss_map), Colors.MAGENTA)
        print_ss_table_pretty(ss_map)

        print()
    
    elif args.command == 'cs':
        cs_map = read_cs_table()
        if args.index is not None:
            print()
            print_cs_table_pretty(cs_map, single_index=args.index)
            print()
        else:
            print_section_header("CRITICAL SPAN TABLE", CS_TABLE_PATH, len(cs_map), Colors.GREEN)
            print_cs_table_pretty(cs_map)
            print()
    
    elif args.command == 'ss':
        ss_map = read_ss_table()
        if args.index is not None:
            print()
            print_ss_table_pretty(ss_map, single_index=args.index)
            print()
        else:
            print_section_header("SYMBOLIC STATE TABLE", SS_TABLE_PATH, len(ss_map), Colors.MAGENTA)
            print_ss_table_pretty(ss_map)
            print()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
