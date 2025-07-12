#!/usr/bin/env python3
"""
Enhanced script to analyze changes of any symbol in git history.
This script can process git log output from stdin or run git commands directly.
Supports multithreading for faster analysis by dividing version ranges among threads.
"""

import subprocess
import re
import sys
import argparse
import os
from typing import List, Dict, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
from datetime import datetime

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
parser.add_argument('--very-verbose', '-vv', action='store_true',
                    help='Show very verbose output including full commit diff and detailed context')
parser.add_argument('--threads', '-t', type=int, default=4,
                    help='Number of threads for parallel processing (default: 4)')
parser.add_argument('--filter-duplicates', '-d', action='store_true',
                    help='Filter commits that only change line numbers but not the actual definition value')

args = parser.parse_args()

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

# Global lock for thread-safe printing
print_lock = Lock()

def colored_print(text: str, color: str = Colors.END, bold: bool = False):
    """Print colored text in a thread-safe manner."""
    with print_lock:
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

def get_commit_date(commit_hash: str, kernel_path: Optional[str] = None) -> Optional[datetime]:
    """Get commit date as datetime object for sorting."""
    cmd = ['git', 'log', '--format=format:%ad', '--date=iso', '-1', commit_hash]
    output = run_git_command(cmd, kernel_path)
    if output.strip():
        try:
            return datetime.fromisoformat(output.strip().replace('Z', '+00:00'))
        except ValueError:
            return None
    return None

def get_commit_diff(commit_hash: str, kernel_path: Optional[str] = None) -> str:
    """Get the full diff of a commit."""
    cmd = ['git', 'show', '--stat', commit_hash]
    return run_git_command(cmd, kernel_path)

def get_commit_full_message(commit_hash: str, kernel_path: Optional[str] = None) -> str:
    """Get the full commit message including body."""
    cmd = ['git', 'log', '--format=format:%B', '-1', commit_hash]
    return run_git_command(cmd, kernel_path)

def normalize_definition(definition: str) -> str:
    """Normalize definition by removing whitespace and comments to compare content."""
    if not definition:
        return ""
    
    # Remove comments and extra whitespace
    lines = definition.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Remove comments (both // and /* */)
        line = re.sub(r'//.*$', '', line)  # Remove // comments
        line = re.sub(r'/\*.*?\*/', '', line)  # Remove /* */ comments
        line = line.strip()
        if line:
            normalized_lines.append(line)
    
    return ' '.join(normalized_lines)

def definitions_are_equivalent(def1: str, def2: str) -> bool:
    """Compare two definitions to see if they are equivalent (ignoring position/line numbers)."""
    if not def1 or not def2:
        return False
    
    # Normalize both definitions
    norm1 = normalize_definition(def1)
    norm2 = normalize_definition(def2)
    
    return norm1 == norm2

def analyze_version_range(args: Tuple[str, str, str, str, Optional[str], bool, bool, int, int]) -> List[Dict]:
    """Analyze a specific version range. This function is designed to be run in a thread."""
    start_version, end_version, symbol, file_path, kernel_path, verbose, very_verbose, thread_id, total_threads = args
    
    results = []
    
    try:
        # Get git log for this version range
        git_log_cmd = [
            'git', 'log', '--full-history', '-S', symbol,
            f'{start_version}..{end_version}', '--', file_path
        ]
        
        git_log_output = run_git_command(git_log_cmd, kernel_path)
        
        if not git_log_output.strip():
            colored_print(f"Thread {thread_id}: No changes found in range {start_version}..{end_version}", Colors.YELLOW)
            return results
        
        commit_hashes = get_commit_hashes(git_log_output)
        
        if not commit_hashes:
            colored_print(f"Thread {thread_id}: No relevant commits found in range {start_version}..{end_version}", Colors.YELLOW)
            return results
        
        colored_print(f"Thread {thread_id}: Found {len(commit_hashes)} commits in range {start_version}..{end_version}", Colors.GREEN)
        
        # Analyze each commit in this range
        for i, commit_hash in enumerate(commit_hashes):
            result = {
                'commit_hash': commit_hash,
                'found': False,
                'definition': None,
                'definition_file': file_path,
                'line_number': None,
                'context': None,
                'commit_info': None,
                'error': None,
                'thread_id': thread_id
            }
            
            try:
                # Get commit info
                commit_info = get_commit_info(commit_hash, kernel_path)
                result['commit_info'] = commit_info
                
                # Get commit date for sorting
                commit_date = get_commit_date(commit_hash, kernel_path)
                result['commit_date'] = commit_date
                
                # First try to get file content from the specified file
                content = get_file_content_at_commit(commit_hash, file_path, kernel_path)
                definition = None
                definition_file = file_path
                line_number = None
                context = None
                
                if content:
                    if verbose:
                        result_ctx = find_symbol_definition_with_context(content, symbol)
                        if result_ctx:
                            definition, line_number, context = result_ctx
                    else:
                        definition = find_symbol_definition(content, symbol)
                
                # If not found in the specified file, check files in the commit diff
                if not definition and kernel_path:
                    diff_result = find_symbol_in_commit_diff(commit_hash, symbol, kernel_path, verbose)
                    if diff_result:
                        if verbose:
                            definition_file, definition, line_number, context = diff_result
                        else:
                            definition_file, definition = diff_result
                
                if definition:
                    result['found'] = True
                    result['definition'] = definition
                    result['definition_file'] = definition_file
                    result['line_number'] = line_number
                    result['context'] = context
                    
            except Exception as e:
                result['error'] = str(e)
            
            results.append(result)
            
    except Exception as e:
        colored_print(f"Thread {thread_id}: Error processing range {start_version}..{end_version}: {e}", Colors.RED)
    
    return results

def get_version_ranges(start_version: str, end_version: str, num_threads: int, kernel_path: Optional[str] = None) -> List[Tuple[str, str]]:
    """Divide version range into non-overlapping, ordered sub-ranges for each thread (only formal releases)."""
    if num_threads == 1:
        return [(start_version, end_version)]
    
    # Get all tags between start and end versions
    cmd = ['git', 'tag', '--list', '--sort=version:refname']
    all_tags_output = run_git_command(cmd, kernel_path)
    
    if not all_tags_output:
        return [(start_version, end_version)]
    
    # Parse tags and filter by version range, only keep formal releases
    all_tags = [tag.strip() for tag in all_tags_output.strip().split('\n') if tag.strip()]
    filtered_tags = []
    for tag in all_tags:
        if tag >= start_version and tag <= end_version:
            if re.match(r'^v\d+\.\d+$', tag):
                filtered_tags.append(tag)
    
    # Add start and end versions if not already present
    if start_version not in filtered_tags:
        filtered_tags.insert(0, start_version)
    if end_version not in filtered_tags:
        filtered_tags.append(end_version)
    
    # Sort tags
    filtered_tags = sorted(set(filtered_tags), key=lambda x: [int(i) for i in x[1:].split('.')])
    
    # If区间数大于tag数，直接每个区间只分配一个tag
    if len(filtered_tags) <= num_threads:
        return [(filtered_tags[i], filtered_tags[i+1]) for i in range(len(filtered_tags)-1)]
    
    # 均匀划分区间
    step = (len(filtered_tags) - 1) // num_threads
    remainder = (len(filtered_tags) - 1) % num_threads
    ranges = []
    idx = 0
    for i in range(num_threads):
        next_idx = idx + step + (1 if i < remainder else 0)
        start = filtered_tags[idx]
        end = filtered_tags[next_idx]
        ranges.append((start, end))
        idx = next_idx
    return ranges

def analyze_from_git_log_output(git_log_output: str, symbol: str, file_path: str = 'kernel/rcu/tree.c', 
                               kernel_path: Optional[str] = None, verbose: bool = False, max_workers: int = 4):
    """Analyze symbol changes from git log output using multithreading by version ranges."""
    colored_print(f"Analyzing {symbol} changes in git history...", Colors.HEADER, bold=True)
    if kernel_path:
        colored_print(f"Using kernel source path: {kernel_path}", Colors.CYAN)
    colored_print(f"Using {max_workers} threads for parallel processing", Colors.CYAN)
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
    
    # Analyze each commit (fallback to original method for git log input)
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
                           kernel_path: Optional[str] = None, verbose: bool = False, very_verbose: bool = False, 
                           max_workers: int = 4, filter_duplicates: bool = False):
    """Run git command and analyze the output using version range multithreading."""
    colored_print(f"Analyzing {symbol} changes from {start_version} to {end_version}...", Colors.HEADER, bold=True)
    if kernel_path:
        colored_print(f"Using kernel source path: {kernel_path}", Colors.CYAN)
    colored_print(f"Using {max_workers} threads for parallel processing", Colors.CYAN)
    if filter_duplicates:
        colored_print("Filtering duplicate definitions (keeping earliest commit)", Colors.CYAN)
    print("=" * 80)
    
    # Divide version range into sub-ranges
    version_ranges = get_version_ranges(start_version, end_version, max_workers, kernel_path)
    
    colored_print(f"Divided version range into {len(version_ranges)} sub-ranges:", Colors.CYAN)
    for i, (start_ver, end_ver) in enumerate(version_ranges):
        colored_print(f"  Thread {i+1}: {start_ver}..{end_ver}", Colors.CYAN)
    print()
    
    # Prepare arguments for thread pool
    thread_args = []
    for i, (start_ver, end_ver) in enumerate(version_ranges):
        thread_args.append((start_ver, end_ver, symbol, file_path, kernel_path, verbose, very_verbose, i + 1, max_workers))
    
    # Process version ranges in parallel
    start_time = time.time()
    all_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_range = {executor.submit(analyze_version_range, args): args for args in thread_args}
        
        # Process completed tasks
        for future in as_completed(future_to_range):
            range_args = future_to_range[future]
            start_ver, end_ver = range_args[0], range_args[1]
            thread_id = range_args[6]
            
            try:
                results = future.result()
                all_results.extend(results)
                
                # Print progress
                colored_print(f"Thread {thread_id} completed: {start_ver}..{end_ver} ({len(results)} commits)", Colors.BLUE)
                
            except Exception as e:
                colored_print(f"Error in thread {thread_id} processing range {start_ver}..{end_ver}: {e}", Colors.RED)
    
    # Sort results by commit date
    all_results.sort(key=lambda x: x.get('commit_date', datetime.min))
    
    # Filter duplicate definitions if requested
    if filter_duplicates:
        filtered_results = []
        seen_definitions = {}
        
        for result in all_results:
            if not result['found'] or not result['definition']:
                filtered_results.append(result)
                continue
            
            definition = result['definition']
            normalized_def = normalize_definition(definition)
            
            if normalized_def not in seen_definitions:
                # First time seeing this definition
                seen_definitions[normalized_def] = result
                filtered_results.append(result)
                colored_print(f"Keeping first occurrence of definition: {normalized_def[:50]}...", Colors.GREEN)
            else:
                # Duplicate definition found
                original_commit = seen_definitions[normalized_def]['commit_hash']
                current_commit = result['commit_hash']
                colored_print(f"Filtering duplicate definition in commit {current_commit} (same as {original_commit})", Colors.YELLOW)
        
        all_results = filtered_results
    
    # Print results
    colored_print(f"\nAnalysis completed in {time.time() - start_time:.2f} seconds", Colors.GREEN, bold=True)
    colored_print(f"Total commits analyzed: {len(all_results)}", Colors.GREEN, bold=True)
    if filter_duplicates:
        colored_print(f"Filtered duplicate definitions: {len(seen_definitions) if 'seen_definitions' in locals() else 0} unique definitions", Colors.GREEN, bold=True)
    print()
    
    for i, result in enumerate(all_results):
        commit_hash = result['commit_hash']
        thread_id = result.get('thread_id', 'N/A')
        
        colored_print(f"Commit {i+1}/{len(all_results)} (Thread {thread_id}): {commit_hash}", Colors.BLUE, bold=True)
        
        if result['error']:
            colored_print(f"Error: {result['error']}", Colors.RED)
            print("-" * 80)
            print()
            continue
        
        # Print commit info
        commit_info = result['commit_info']
        if commit_info:
            colored_print(f"Author: {commit_info['author']}", Colors.CYAN)
            colored_print(f"Date: {commit_info['date']}", Colors.CYAN)
            colored_print(f"Message: {commit_info['message']}", Colors.CYAN)
        
        # Print very verbose information if requested
        if very_verbose:
            commit_hash = result['commit_hash']
            
            # Get full commit message
            full_message = get_commit_full_message(commit_hash, kernel_path)
            if full_message:
                colored_print("Full commit message:", Colors.HEADER, bold=True)
                print("-" * 40)
                print(full_message.strip())
                print("-" * 40)
                print()
        
        if result['found']:
            if verbose and result['line_number']:
                colored_print(f"{symbol} definition (line {result['line_number']}):", Colors.GREEN, bold=True)
            else:
                colored_print(f"{symbol} definition:", Colors.GREEN, bold=True)
            print(f"  {result['definition']}")
            if verbose and result['context']:
                colored_print("  Context:", Colors.CYAN)
                print(f"  {result['context']}")
        else:
            colored_print(f"  No definition found for {symbol}", Colors.RED)
        
        print("-" * 80)
        print()

def main():
    """Main entry point."""
    
    # Expand user paths
    if args.kernel_path:
        args.kernel_path = os.path.expanduser(args.kernel_path)
    if args.file_path:
        args.file_path = os.path.expanduser(args.file_path)
    
    # Validate thread count
    if args.threads < 1:
        colored_print("Thread count must be at least 1, using 1 thread", Colors.YELLOW)
        args.threads = 1
    elif args.threads > 16:
        colored_print("Thread count capped at 16 for stability", Colors.YELLOW)
        args.threads = 16
    
    try:
        if args.run_git:
            analyze_from_git_command(args.symbol, args.file_path, args.start_version, args.end_version, 
                                   args.kernel_path, args.verbose, args.very_verbose, args.threads, args.filter_duplicates)
        elif args.input:
            if args.input == '-':
                # Read from stdin
                git_log_output = sys.stdin.read()
            else:
                # Read from file
                with open(args.input, 'r') as f:
                    git_log_output = f.read()
            analyze_from_git_log_output(git_log_output, args.symbol, args.file_path, args.kernel_path, 
                                      args.verbose, args.threads)
        else:
            # Default: run git command
            analyze_from_git_command(args.symbol, args.file_path, args.start_version, args.end_version, 
                                   args.kernel_path, args.verbose, args.very_verbose, args.threads, args.filter_duplicates)
            
    except KeyboardInterrupt:
        colored_print("\nAnalysis interrupted by user", Colors.YELLOW)
    except Exception as e:
        colored_print(f"Error during analysis: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main() 