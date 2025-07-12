#!/usr/bin/env python3
"""
Enhanced script to analyze changes of any symbol in git history.
This script can process git log output from stdin or run git commands directly.
"""

import subprocess
import re
import sys
import argparse
import os
from typing import List, Dict, Optional, Union

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colored_print(text: str, color: str = Colors.END, bold: bool = False):
    """Print colored text."""
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.END}")
    else:
        print(f"{color}{text}{Colors.END}")

def run_git_command(cmd: List[str], kernel_path: Optional[str] = None) -> str:
    """Run a git command and return the output."""
    try:
        if kernel_path:
            # Save current directory
            original_dir = os.getcwd()
            try:
                # Change to kernel directory
                os.chdir(kernel_path)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout
            finally:
                # Restore original directory
                os.chdir(original_dir)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
    except subprocess.CalledProcessError as e:
        colored_print(f"Error running git command: {e}", Colors.RED)
        return ""

def get_commit_hashes(git_log_output: str) -> List[str]:
    """Extract commit hashes from git log output."""
    commit_hashes = []
    lines = git_log_output.strip().split('\n')
    
    for line in lines:
        if line.startswith('commit '):
            commit_hash = line.split()[1]
            commit_hashes.append(commit_hash)
    
    return commit_hashes

def get_file_content_at_commit(commit_hash: str, file_path: str, kernel_path: Optional[str] = None) -> str:
    """Get the content of a file at a specific commit."""
    cmd = ['git', 'show', f'{commit_hash}:{file_path}']
    return run_git_command(cmd, kernel_path)

def find_symbol_definition(content: str, symbol: str) -> Optional[str]:
    """Find the definition of a symbol in the content."""
    lines = content.split('\n')
    
    # Look for different types of definitions
    patterns = [
        rf'#define\s+{re.escape(symbol)}\s+.*',
        rf'#define\s+{re.escape(symbol)}\s*$',
        rf'static\s+.*\s+{re.escape(symbol)}\s*=.*',
        rf'const\s+.*\s+{re.escape(symbol)}\s*=.*',
        rf'{re.escape(symbol)}\s*=.*',
    ]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Get the full definition (might span multiple lines)
                definition = line.strip()
                
                # If it's a multi-line definition, get the next few lines
                if line.strip().endswith('\\') or line.strip().endswith('{'):
                    j = i + 1
                    while j < len(lines) and (lines[j].strip().endswith('\\') or 
                                             (lines[j].strip() and not lines[j].strip().endswith(';'))):
                        definition += '\n' + lines[j].strip()
                        j += 1
                        if j - i > 5:  # Limit to avoid too long definitions
                            break
                
                return definition
    
    return None

def find_symbol_definition_with_context(content: str, symbol: str) -> Optional[tuple]:
    """Find the definition of a symbol in the content with context."""
    lines = content.split('\n')
    
    # Look for different types of definitions
    patterns = [
        rf'#define\s+{re.escape(symbol)}\s+.*',
        rf'#define\s+{re.escape(symbol)}\s*$',
        rf'static\s+.*\s+{re.escape(symbol)}\s*=.*',
        rf'const\s+.*\s+{re.escape(symbol)}\s*=.*',
        rf'{re.escape(symbol)}\s*=.*',
    ]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Get the full definition (might span multiple lines)
                definition = line.strip()
                line_number = i + 1
                
                # If it's a multi-line definition, get the next few lines
                if line.strip().endswith('\\') or line.strip().endswith('{'):
                    j = i + 1
                    while j < len(lines) and (lines[j].strip().endswith('\\') or 
                                             (lines[j].strip() and not lines[j].strip().endswith(';'))):
                        definition += '\n' + lines[j].strip()
                        j += 1
                        if j - i > 5:  # Limit to avoid too long definitions
                            break
                
                # Get context (a few lines before and after)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context_lines = []
                
                for ctx_i in range(context_start, context_end):
                    prefix = ">>> " if ctx_i == i else "    "
                    context_lines.append(f"{prefix}{ctx_i + 1:4d}: {lines[ctx_i]}")
                
                return (definition, line_number, '\n'.join(context_lines))
    
    return None

def find_symbol_in_commit_diff(commit_hash: str, symbol: str, kernel_path: Optional[str] = None, verbose: bool = False) -> Optional[tuple]:
    """Find symbol definition by analyzing commit diff to see where it was moved."""
    if not kernel_path:
        return None
    
    # Get the commit diff with file names only
    cmd = ['git', 'show', '--name-only', '--format=', commit_hash]
    diff_output = run_git_command(cmd, kernel_path)
    
    # Parse the diff to find files that contain the symbol
    lines = diff_output.strip().split('\n')
    files_to_check = []
    
    for line in lines:
        line = line.strip()
        # Only consider lines that look like file paths (not empty, not starting with common prefixes)
        if line and not line.startswith('commit') and not line.startswith('Author') and not line.startswith('Date') and not line.startswith('diff') and not line.startswith('index') and not line.startswith('---') and not line.startswith('+++') and not line.startswith('Signed-off-by') and not line.startswith('Acked-by') and not line.startswith('Tested-by') and not line.startswith('Reviewed-by'):
            # Check if it looks like a file path (contains / or .)
            if '/' in line or line.endswith('.c') or line.endswith('.h'):
                files_to_check.append(line)
    
    # Check each file in the commit for the symbol definition
    for file_path in files_to_check:
        if file_path:
            content = get_file_content_at_commit(commit_hash, file_path, kernel_path)
            if content:
                if verbose:
                    result = find_symbol_definition_with_context(content, symbol)
                    if result:
                        definition, line_number, context = result
                        return (file_path, definition, line_number, context)
                else:
                    definition = find_symbol_definition(content, symbol)
                    if definition:
                        return (file_path, definition)
    
    return None

def get_commit_info(commit_hash: str, kernel_path: Optional[str] = None) -> Dict[str, str]:
    """Get commit information including author, date, and message."""
    cmd = ['git', 'log', '--format=format:%H%n%an%n%ad%n%s', '-1', commit_hash]
    output = run_git_command(cmd, kernel_path)
    lines = output.strip().split('\n')
    
    if len(lines) >= 4:
        return {
            'hash': lines[0],
            'author': lines[1],
            'date': lines[2],
            'message': lines[3]
        }
    return {}

def analyze_from_git_log_output(git_log_output: str, symbol: str, file_path: str = 'kernel/rcu/tree.c', kernel_path: Optional[str] = None, verbose: bool = False):
    """Analyze symbol changes from git log output."""
    colored_print(f"Analyzing {symbol} changes in git history...", Colors.HEADER, bold=True)
    if kernel_path:
        colored_print(f"Using kernel source path: {kernel_path}", Colors.CYAN)
    print("=" * 80)
    
    if not git_log_output.strip():
        colored_print(f"No changes found for {symbol}", Colors.YELLOW)
        return
    
    commit_hashes = get_commit_hashes(git_log_output)
    
    if not commit_hashes:
        colored_print("No relevant commits found", Colors.YELLOW)
        return
    
    colored_print(f"Found {len(commit_hashes)} relevant commits", Colors.GREEN, bold=True)
    print()
    
    # Analyze each commit
    for i, commit_hash in enumerate(commit_hashes):
        colored_print(f"Commit {i+1}/{len(commit_hashes)}: {commit_hash}", Colors.BLUE, bold=True)
        
        # Get commit info
        commit_info = get_commit_info(commit_hash, kernel_path)
        if commit_info:
            colored_print(f"Author: {commit_info['author']}", Colors.CYAN)
            colored_print(f"Date: {commit_info['date']}", Colors.CYAN)
            colored_print(f"Message: {commit_info['message']}", Colors.CYAN)
        
        # First try to get file content from the specified file
        content = get_file_content_at_commit(commit_hash, file_path, kernel_path)
        definition = None
        definition_file = file_path
        line_number = None
        context = None
        
        if content:
            if verbose:
                result = find_symbol_definition_with_context(content, symbol)
                if result:
                    definition, line_number, context = result
            else:
                definition = find_symbol_definition(content, symbol)
        
        # If not found in the specified file, check files in the commit diff
        if not definition and kernel_path:
            colored_print(f"  Symbol not found in {file_path}, checking files in commit diff...", Colors.YELLOW)
            result = find_symbol_in_commit_diff(commit_hash, symbol, kernel_path, verbose)
            if result:
                if verbose:
                    definition_file, definition, line_number, context = result
                else:
                    definition_file, definition = result
                colored_print(f"  Found in file: {definition_file}", Colors.GREEN)
        
        if definition:
            if verbose and line_number:
                colored_print(f"{symbol} definition (line {line_number}):", Colors.GREEN, bold=True)
            else:
                colored_print(f"{symbol} definition:", Colors.GREEN, bold=True)
            print(f"  {definition}")
            if verbose and context:
                colored_print("  Context:", Colors.CYAN)
                print(f"  {context}")
        else:
            colored_print(f"  No definition found for {symbol}", Colors.RED)
        
        print("-" * 80)
        print()

def analyze_from_git_command(symbol: str, file_path: str = 'kernel/rcu/tree.c', 
                           start_version: str = 'v5.1', end_version: str = 'v6.14',
                           kernel_path: Optional[str] = None, verbose: bool = False):
    """Run git command and analyze the output."""
    git_log_cmd = [
        'git', 'log', '--full-history', '-S', symbol,
        f'{start_version}..{end_version}', '--', file_path
    ]
    
    git_log_output = run_git_command(git_log_cmd, kernel_path)
    analyze_from_git_log_output(git_log_output, symbol, file_path, kernel_path, verbose)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze symbol changes in git history')
    parser.add_argument('symbol', help='Symbol to search for (e.g., KFREE_DRAIN_JIFFIES)')
    parser.add_argument('--input', '-i', help='Read git log output from file (use - for stdin)')
    parser.add_argument('--file-path', '-f', default='kernel/rcu/tree.c', 
                       help='Path to the file containing the symbol (relative to kernel source)')
    parser.add_argument('--start-version', '-s', default='v5.1',
                       help='Start version/tag for git range (default: v5.1)')
    parser.add_argument('--end-version', '-e', default='v6.14',
                       help='End version/tag for git range (default: v6.14)')
    parser.add_argument('--kernel-path', '-k', required=True,
                       help='Path to kernel source code directory')
    parser.add_argument('--run-git', '-g', action='store_true', 
                       help='Run git command directly instead of reading from input')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output including line numbers and context')
    
    args = parser.parse_args()
    
    # Expand user paths
    if args.kernel_path:
        args.kernel_path = os.path.expanduser(args.kernel_path)
    if args.file_path:
        args.file_path = os.path.expanduser(args.file_path)
    
    try:
        if args.run_git:
            analyze_from_git_command(args.symbol, args.file_path, args.start_version, args.end_version, args.kernel_path, args.verbose)
        elif args.input:
            if args.input == '-':
                # Read from stdin
                git_log_output = sys.stdin.read()
            else:
                # Read from file
                with open(args.input, 'r') as f:
                    git_log_output = f.read()
            analyze_from_git_log_output(git_log_output, args.symbol, args.file_path, args.kernel_path, args.verbose)
        else:
            # Default: run git command
            analyze_from_git_command(args.symbol, args.file_path, args.start_version, args.end_version, args.kernel_path, args.verbose)
            
    except KeyboardInterrupt:
        colored_print("\nAnalysis interrupted by user", Colors.YELLOW)
    except Exception as e:
        colored_print(f"Error during analysis: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main() 