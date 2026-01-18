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
from typing import List, Dict, Optional

SCOPE_TABLE_PATH = "/dev/shm/xkernel/scope_table"
CS_TABLE_PATH = "/dev/shm/xkernel/cs_table"
SS_TABLE_PATH = "/dev/shm/xkernel/ss_table"

SCOPE_TABLE_HEADER = ["ConstID", "Val", "Expression", "CS_Index", "SS_Index", "Status"]
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
                    'Status': row[5].strip() if len(row) > 5 else ""
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
        print("Scope Table does not exist.")
        return 0
    
    entries = read_scope_table()
    
    if delete_all:
        if not entries:
            print("Scope Table is already empty.")
            return 0
        count = len(entries)
        write_scope_table([])
        print(f"Deleted all {count} entries from Scope Table.")
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
        print(f"Deleted {deleted_count} entry/entries from Scope Table.")
    else:
        print("No matching entries found to delete.")
    
    return deleted_count


def print_entries(entries: List[Dict[str, str]], show_header: bool = True, show_content: bool = True):
    """Print entries in a formatted table.
    
    Args:
        entries: List of entries to print
        show_header: Whether to show the header row
        show_content: If True, show CS and SS content; if False, show only indices
    """
    if not entries:
        print("No entries found.")
        return
    
    # Calculate column widths
    if show_content:
        widths = {
            'ConstID': max(len('ConstID'), max(len(e.get('ConstID', '')) for e in entries)),
            'Val': max(len('Val'), max(len(e.get('Val', '')) for e in entries)),
            'Expression': max(len('Expression'), max(len(e.get('Expression', '')) for e in entries)),
            'CS': max(len('CS'), max(len(e.get('CS', '')) for e in entries), 50),
            'SS': max(len('SS'), max(len(e.get('SS', '')) for e in entries), 30),
            'Status': max(len('Status'), max(len(e.get('Status', '')) for e in entries))
        }
    else:
        widths = {
            'ConstID': max(len('ConstID'), max(len(e.get('ConstID', '')) for e in entries)),
            'Val': max(len('Val'), max(len(e.get('Val', '')) for e in entries)),
            'Expression': max(len('Expression'), max(len(e.get('Expression', '')) for e in entries)),
            'CS_Index': max(len('CS_Index'), max(len(e.get('CS_Index', '')) for e in entries)),
            'SS_Index': max(len('SS_Index'), max(len(e.get('SS_Index', '')) for e in entries)),
            'Status': max(len('Status'), max(len(e.get('Status', '')) for e in entries))
        }
    
    # Print header
    if show_header:
        if show_content:
            header = f"{'ConstID':<{widths['ConstID']}}  {'Val':<{widths['Val']}}  {'Expression':<{widths['Expression']}}  {'CS':<{widths['CS']}}  {'SS':<{widths['SS']}}  {'Status':<{widths['Status']}}"
        else:
            header = f"{'ConstID':<{widths['ConstID']}}  {'Val':<{widths['Val']}}  {'Expression':<{widths['Expression']}}  {'CS_Index':<{widths['CS_Index']}}  {'SS_Index':<{widths['SS_Index']}}  {'Status':<{widths['Status']}}"
        print(header)
        print('-' * len(header))
    
    # Print entries
    for entry in entries:
        if show_content:
            # Truncate long CS/SS content for display
            cs_display = entry.get('CS', '')
            ss_display = entry.get('SS', '')
            if len(cs_display) > 60:
                cs_display = cs_display[:57] + "..."
            if len(ss_display) > 30:
                ss_display = ss_display[:27] + "..."
            
            print(f"{entry.get('ConstID', ''):<{widths['ConstID']}}  "
                  f"{entry.get('Val', ''):<{widths['Val']}}  "
                  f"{entry.get('Expression', ''):<{widths['Expression']}}  "
                  f"{cs_display:<{widths['CS']}}  "
                  f"{ss_display:<{widths['SS']}}  "
                  f"{entry.get('Status', ''):<{widths['Status']}}")
        else:
            print(f"{entry.get('ConstID', ''):<{widths['ConstID']}}  "
                  f"{entry.get('Val', ''):<{widths['Val']}}  "
                  f"{entry.get('Expression', ''):<{widths['Expression']}}  "
                  f"{entry.get('CS_Index', ''):<{widths['CS_Index']}}  "
                  f"{entry.get('SS_Index', ''):<{widths['SS_Index']}}  "
                  f"{entry.get('Status', ''):<{widths['Status']}}")


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
                            'Status': row[5].strip() if len(row) > 5 else ""
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
        print_entries(raw_entries, show_content=False)
    
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
        # Show Scope Table (always show indices, not content)
        # Read raw entries without resolving CS/SS content
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
                            'Status': row[5].strip() if len(row) > 5 else ""
                        })
        
        print(f"\n{'='*80}")
        print(f"Scope Table: {SCOPE_TABLE_PATH}")
        print(f"{'='*80}")
        print(f"Total entries: {len(raw_entries)}\n")
        print_entries(raw_entries, show_content=False)
        
        # Show CS Table
        cs_map = read_cs_table()
        print(f"\n{'='*80}")
        print(f"CS Table: {CS_TABLE_PATH}")
        print(f"{'='*80}")
        print(f"Total entries: {len(cs_map)}\n")
        if cs_map:
            for index in sorted(cs_map.keys()):
                content = cs_map[index]
                # Split by semicolon and print each instruction on a separate line
                instructions = [inst.strip() for inst in content.split(';') if inst.strip()]
                if instructions:
                    print(f"  [{index}]")
                    for inst in instructions:
                        print(f"      {inst}")
                else:
                    print(f"  [{index}] {content}")
        else:
            print("No entries found.")
        
        # Show SS Table
        ss_map = read_ss_table()
        print(f"\n{'='*80}")
        print(f"SS Table: {SS_TABLE_PATH}")
        print(f"{'='*80}")
        print(f"Total entries: {len(ss_map)}\n")
        if ss_map:
            for index in sorted(ss_map.keys()):
                content = ss_map[index]
                if len(content) > 80:
                    content = content[:77] + "..."
                print(f"  [{index}] {content}")
        else:
            print("No entries found.")
        print()
    
    elif args.command == 'cs':
        cs_map = read_cs_table()
        if args.index:
            if args.index in cs_map:
                content = cs_map[args.index]
                # Split by semicolon and print each instruction on a separate line
                instructions = [inst.strip() for inst in content.split(';') if inst.strip()]
                if instructions:
                    print(f"CS[{args.index}]:")
                    for inst in instructions:
                        print(f"  {inst}")
                else:
                    print(f"CS[{args.index}]: {content}")
            else:
                print(f"CS index {args.index} not found.")
        else:
            print(f"\nCS Table: {CS_TABLE_PATH}")
            print(f"Total entries: {len(cs_map)}\n")
            if cs_map:
                for index in sorted(cs_map.keys()):
                    content = cs_map[index]
                    # Split by semicolon and print each instruction on a separate line
                    instructions = [inst.strip() for inst in content.split(';') if inst.strip()]
                    if instructions:
                        print(f"  [{index}]")
                        for inst in instructions:
                            print(f"      {inst}")
                    else:
                        print(f"  [{index}] {content}")
            else:
                print("No entries found.")
    
    elif args.command == 'ss':
        ss_map = read_ss_table()
        if args.index:
            if args.index in ss_map:
                print(f"SS[{args.index}]: {ss_map[args.index]}")
            else:
                print(f"SS index {args.index} not found.")
        else:
            print(f"\nSS Table: {SS_TABLE_PATH}")
            print(f"Total entries: {len(ss_map)}\n")
            if ss_map:
                for index in sorted(ss_map.keys()):
                    content = ss_map[index]
                    if len(content) > 80:
                        content = content[:77] + "..."
                    print(f"  [{index}] {content}")
            else:
                print("No entries found.")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
