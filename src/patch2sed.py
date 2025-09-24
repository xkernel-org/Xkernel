#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script is used to patch the source code by using sed commands.
import sys
import os
import re
import subprocess

def parse_patch(patch_file, reverse=False):
    """Parse patch file and extract changes
    
    Args:
        patch_file: Path to the patch file
        reverse: If True, reverse the patch (for undo operation)
    """
    changes = []
    
    with open(patch_file, 'r') as f:
        lines = f.readlines()
    
    current_file = None
    current_line_num = None
    in_hunk = False
    pending_remove = None
    
    for line in lines:
        line = line.rstrip('\n')
        
        # Extract file path from diff header
        if line.startswith('--- a/'):
            current_file = line[6:]  # Remove '--- a/'
        elif line.startswith('+++ b/'):
            # Skip the +++ line, we already have the file path
            continue
        elif line.startswith('@@'):
            # Extract line number from hunk header
            match = re.search(r'@@ -\d+,?\d* \+(\d+),?\d* @@', line)
            if match:
                current_line_num = int(match.group(1))
                in_hunk = True
        elif in_hunk and line.startswith('-'):
            # This is a line to be removed (or added in reverse mode)
            content = line[1:]  # Remove the '-' prefix
            if reverse:
                # In reverse mode, '-' lines become additions
                if pending_remove:
                    # This is a replacement (add + remove in reverse)
                    changes.append({
                        'file': current_file,
                        'line_num': pending_remove['line_num'],
                        'type': 'replace',
                        'old_content': pending_remove['content'],
                        'new_content': content
                    })
                    pending_remove = None
                else:
                    # This is just an addition in reverse mode
                    changes.append({
                        'file': current_file,
                        'line_num': current_line_num,
                        'type': 'add',
                        'content': content
                    })
                current_line_num += 1
            else:
                # Normal mode: this is a line to be removed
                pending_remove = {
                    'file': current_file,
                    'line_num': current_line_num,
                    'content': content
                }
                current_line_num += 1
        elif in_hunk and line.startswith('+'):
            # This is a line to be added (or removed in reverse mode)
            content = line[1:]  # Remove the '+' prefix
            if reverse:
                # In reverse mode, '+' lines become removals
                if pending_remove:
                    # This is a replacement (remove + add in reverse)
                    changes.append({
                        'file': current_file,
                        'line_num': pending_remove['line_num'],
                        'type': 'replace',
                        'old_content': content,
                        'new_content': pending_remove['content']
                    })
                    pending_remove = None
                else:
                    # This is just a removal in reverse mode
                    changes.append({
                        'file': current_file,
                        'line_num': current_line_num,
                        'type': 'remove',
                        'content': content
                    })
                current_line_num += 1
            else:
                # Normal mode: this is a line to be added
                if pending_remove:
                    # This is a replacement (remove + add)
                    changes.append({
                        'file': current_file,
                        'line_num': pending_remove['line_num'],
                        'type': 'replace',
                        'old_content': pending_remove['content'],
                        'new_content': content
                    })
                    pending_remove = None
                else:
                    # This is just an addition
                    changes.append({
                        'file': current_file,
                        'line_num': current_line_num,
                        'type': 'add',
                        'content': content
                    })
                current_line_num += 1
        elif in_hunk and line.startswith(' '):
            # This is a context line
            if pending_remove:
                # We have a pending remove without a corresponding add, so it's a deletion
                changes.append({
                    'file': current_file,
                    'line_num': pending_remove['line_num'],
                    'type': 'remove',
                    'content': pending_remove['content']
                })
                pending_remove = None
            current_line_num += 1
        elif in_hunk and line == '':
            # Empty line in hunk
            if pending_remove:
                # We have a pending remove without a corresponding add, so it's a deletion
                changes.append({
                    'file': current_file,
                    'line_num': pending_remove['line_num'],
                    'type': 'remove',
                    'content': pending_remove['content']
                })
                pending_remove = None
            current_line_num += 1
        elif not line.startswith('diff') and not line.startswith('index'):
            # End of hunk
            if pending_remove:
                # We have a pending remove without a corresponding add, so it's a deletion
                changes.append({
                    'file': current_file,
                    'line_num': pending_remove['line_num'],
                    'type': 'remove',
                    'content': pending_remove['content']
                })
                pending_remove = None
            in_hunk = False
    
    return changes

def apply_changes_with_sed(kernel_path, changes, use_sudo=False):
    """Apply changes using sed commands"""
    
    for change in changes:
        file_path = os.path.join(kernel_path, change['file'])
        
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping...")
            continue
        
        line_num = change['line_num']
        
        # Check if we need sudo
        sudo_prefix = "sudo " if use_sudo else ""
        
        if change['type'] == 'remove':
            # For removal, we need to find the line and remove it
            # Use sed to delete the specific line
            sed_cmd = f"{sudo_prefix}sed -i '{line_num}d' '{file_path}'"
            print(f"Executing: {sed_cmd}")
            try:
                subprocess.run(sed_cmd, shell=True, check=True)
                print(f"Removed line {line_num} from {file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error removing line {line_num} from {file_path}: {e}")
        
        elif change['type'] == 'add':
            # For addition, we need to insert the line at the specified position
            # Use sed to insert the line before the specified line number
            # Escape special characters in the content for sed
            content = change['content']
            escaped_content = content.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
            sed_cmd = f"{sudo_prefix}sed -i '{line_num-1}a\\{escaped_content}' '{file_path}'"
            print(f"Executing: {sed_cmd}")
            try:
                subprocess.run(sed_cmd, shell=True, check=True)
                print(f"Added line at position {line_num} in {file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error adding line at {line_num} in {file_path}: {e}")
        
        elif change['type'] == 'replace':
            # For replacement, we need to replace the specific line
            # Use sed to substitute the line content
            old_content = change['old_content']
            new_content = change['new_content']
            
            # Escape special characters for sed
            escaped_old = old_content.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
            escaped_new = new_content.replace('\\', '\\\\').replace('/', '\\/').replace('&', '\\&')
            
            sed_cmd = f"{sudo_prefix}sed -i '{line_num}s/.*/{escaped_new}/' '{file_path}'"
            print(f"Executing: {sed_cmd}")
            try:
                subprocess.run(sed_cmd, shell=True, check=True)
                print(f"Replaced line {line_num} in {file_path}")
                print(f"  Old: {old_content}")
                print(f"  New: {new_content}")
            except subprocess.CalledProcessError as e:
                print(f"Error replacing line {line_num} in {file_path}: {e}")

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("Usage: python3 patch2sed.py <patch_file> <kernel_path> [--sudo] [-r]")
        print("Example: python3 patch2sed.py blk-throttle.patch /path/to/kernel")
        print("Example: python3 patch2sed.py blk-throttle.patch /path/to/kernel --sudo")
        print("Example: python3 patch2sed.py blk-throttle.patch /path/to/kernel -r")
        print("Example: python3 patch2sed.py blk-throttle.patch /path/to/kernel --sudo -r")
        sys.exit(1)
    
    patch_file = sys.argv[1]
    kernel_path = sys.argv[2]
    
    # Parse optional arguments
    use_sudo = False
    reverse = False
    
    for arg in sys.argv[3:]:
        if arg == '--sudo':
            use_sudo = True
        elif arg == '-r':
            reverse = True
        else:
            print(f"Unknown option: {arg}")
            sys.exit(1)
    
    if not os.path.exists(patch_file):
        print(f"Error: Patch file {patch_file} does not exist")
        sys.exit(1)
    
    if not os.path.exists(kernel_path):
        print(f"Error: Kernel path {kernel_path} does not exist")
        sys.exit(1)
    
    print(f"Reading patch file: {patch_file}")
    print(f"Target kernel path: {kernel_path}")
    if use_sudo:
        print("Using sudo for file modifications")
    if reverse:
        print("Reverting patch (reverse mode)")
    
    # Parse the patch file
    changes = parse_patch(patch_file, reverse)
    
    if not changes:
        print("No changes found in patch file")
        sys.exit(0)
    
    action = "reverting" if reverse else "applying"
    print(f"Found {len(changes)} changes to {action}")
    
    # Apply changes using sed
    apply_changes_with_sed(kernel_path, changes, use_sudo)
    
    action = "revert" if reverse else "application"
    print(f"Patch {action} completed!")

if __name__ == "__main__":
    main()
