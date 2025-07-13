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

cpu_count = os.cpu_count()

parser = argparse.ArgumentParser(description='Analyze symbol changes in git history. Supports multiple symbols via comma-separated list or symbols file.')
parser.add_argument('symbol', nargs='?', help='Symbol to search for (e.g., KFREE_DRAIN_JIFFIES). Can be comma-separated list of symbols.')
parser.add_argument('--symbols-file', '-sf', help='File containing symbols to analyze (one symbol per line)')
parser.add_argument('--start-version', '-s', default='v3.0',
                    help='Start version/tag for git range (default: v3.0)')
parser.add_argument('--end-version', '-e', default='v6.14',
                    help='End version/tag for git range (default: v6.14)')
parser.add_argument('--kernel-path', '-k', required=True,
                    help='Path to kernel source code directory')
parser.add_argument('--verbose', '-v', action='store_true',
                    help='Show verbose output including line numbers and context')
parser.add_argument('--very-verbose', '-vv', action='store_true',
                    help='Show very verbose output including full commit message')
parser.add_argument('--quiet', '-q', action='store_true',
                    help='Quiet mode: only show final analysis results, hide intermediate steps')
parser.add_argument('--threads', '-t', type=int, default=cpu_count,
                    help=f'Number of threads for parallel processing (default: {cpu_count})')
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

def colored_print(text: str, color: str = Colors.END, bold: bool = False, quiet: bool = False):
    """Print colored text in a thread-safe manner."""
    if quiet:
        return
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
        # Don't print error for git log commands that return no results (exit code 128)
        if e.returncode == 128 and 'log' in cmd:
            return ""
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
        rf'#define\s+{re.escape(symbol)}\s*\(.*\)',  # #define SYMBOL(param) ...
        rf'#define\s+{re.escape(symbol)}\s+[^(].*',  # #define SYMBOL value
        rf'#define\s+{re.escape(symbol)}\s*$',       # #define SYMBOL
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
        rf'#define\s+{re.escape(symbol)}\s*\(.*\)',  # #define SYMBOL(param) ...
        rf'#define\s+{re.escape(symbol)}\s+[^(].*',  # #define SYMBOL value
        rf'#define\s+{re.escape(symbol)}\s*$',       # #define SYMBOL
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

def get_commit_kernel_version(commit_hash: str, kernel_path: Optional[str] = None) -> Optional[str]:
    """Get the kernel version tag for a specific commit."""
    try:
        # Find the closest tag before this commit
        cmd = ['git', 'describe', '--tags', '--abbrev=0', commit_hash]
        result = run_git_command(cmd, kernel_path)
        if result.strip():
            return result.strip()
        
        # If no tag found, try to find the next tag after this commit
        cmd = ['git', 'describe', '--tags', '--abbrev=0', '--contains', commit_hash]
        result = run_git_command(cmd, kernel_path)
        if result.strip():
            return result.strip()
        
        return None
    except Exception:
        return None

def parse_symbols_list(symbol_arg: Optional[str], symbols_file: Optional[str]) -> List[Tuple[str, Optional[str]]]:
    """Parse symbols from command line argument or file. Returns list of (symbol, file_path) tuples."""
    symbols = []
    
    # Parse comma-separated symbols from command line
    if symbol_arg:
        # Split by comma, but handle the case where comma is part of the symbol specification
        parts = symbol_arg.split(',')
        i = 0
        while i < len(parts):
            s = parts[i].strip()
            if s:
                # Check if this part contains a file path (next part doesn't look like a symbol)
                if i + 1 < len(parts):
                    next_part = parts[i + 1].strip()
                    # If next part contains a slash, it's likely a file path
                    if '/' in next_part or next_part.endswith('.c') or next_part.endswith('.h'):
                        symbol = s
                        file_path = next_part
                        symbols.append((symbol, file_path))
                        i += 2  # Skip the next part since we used it as file path
                        continue
                
                # No file path specified
                symbols.append((s, None))
            i += 1
    
    # Parse symbols from file
    if symbols_file:
        try:
            with open(symbols_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Check if line has file path specified
                        if ',' in line:
                            parts = line.split(',', 1)
                            symbol = parts[0].strip()
                            file_path = parts[1].strip()
                            symbols.append((symbol, file_path))
                        else:
                            symbols.append((line, None))
        except FileNotFoundError:
            colored_print(f"Error: Symbols file '{symbols_file}' not found", Colors.RED)
            sys.exit(1)
        except Exception as e:
            colored_print(f"Error reading symbols file '{symbols_file}': {e}", Colors.RED)
            sys.exit(1)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_symbols = []
    for symbol, file_path in symbols:
        if symbol not in seen:
            seen.add(symbol)
            unique_symbols.append((symbol, file_path))
    
    return unique_symbols

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

def analyze_version_range(args: Tuple[str, str, str, str, Optional[str], bool, bool, int, int, bool]) -> List[Dict]:
    """Analyze a specific version range. This function is designed to be run in a thread."""
    start_version, end_version, symbol, file_path, kernel_path, verbose, very_verbose, thread_id, total_threads, quiet = args
    
    results = []
    
    try:
        # Get git log for this version range
        git_log_cmd = [
            'git', 'log', '--full-history', '-S', symbol,
            f'{start_version}..{end_version}', '--', file_path
        ]
        
        git_log_output = run_git_command(git_log_cmd, kernel_path)
        
        if not git_log_output.strip():
            if very_verbose and not quiet:
                colored_print(f"Thread {thread_id}: No changes found in range {start_version}..{end_version}", Colors.YELLOW, quiet=quiet)
            return results
        
        commit_hashes = get_commit_hashes(git_log_output)
        
        if not commit_hashes:
            if very_verbose and not quiet:
                colored_print(f"Thread {thread_id}: No relevant commits found in range {start_version}..{end_version}", Colors.YELLOW, quiet=quiet)
            return results
        
        if very_verbose and not quiet:
            colored_print(f"Thread {thread_id}: Found {len(commit_hashes)} commits in range {start_version}..{end_version}", Colors.GREEN, quiet=quiet)
        
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
                
                # Get kernel version for this commit
                kernel_version = get_commit_kernel_version(commit_hash, kernel_path)
                result['kernel_version'] = kernel_version
                
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
    
    # Check if start_version exists, if not find the earliest available version
    if start_version not in filtered_tags and filtered_tags:
        earliest_available = min(filtered_tags, key=lambda x: [int(i) for i in x[1:].split('.')])
        colored_print(f"Warning: Start version {start_version} not found, using earliest available: {earliest_available}", Colors.YELLOW, quiet=args.quiet)
        start_version = earliest_available
    
    # Check if end_version exists, if not find the latest available version
    if end_version not in filtered_tags and filtered_tags:
        latest_available = max(filtered_tags, key=lambda x: [int(i) for i in x[1:].split('.')])
        colored_print(f"Warning: End version {end_version} not found, using latest available: {latest_available}", Colors.YELLOW, quiet=args.quiet)
        end_version = latest_available
    
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

def find_symbol_definition_file(symbol: str, kernel_path: str) -> Optional[str]:
    """Find the file containing the definition of a symbol using git grep."""
    try:
        # Use git grep to find #define statements for the symbol
        cmd = ['git', 'grep', '-nw', f'#define {symbol}']
        result = run_git_command(cmd, kernel_path)
        
        if result.strip():
            # Parse the first line of output to get the file path
            # Format: file_path:line_number:#define SYMBOL_NAME value
            lines = result.strip().split('\n')
            first_line = lines[0]
            
            # Extract file path (everything before the first colon)
            file_path = first_line.split(':', 1)[0]
            
            if not args.quiet:
                colored_print(f"Found {symbol} definition in: {file_path}", Colors.GREEN, quiet=args.quiet)
            return file_path
        else:
            if not args.quiet:
                colored_print(f"No definition found for {symbol} using git grep", Colors.YELLOW, quiet=args.quiet)
            return None
            
    except Exception as e:
        colored_print(f"Error finding definition for {symbol}: {e}", Colors.RED, quiet=args.quiet)
        return None

def analyze_from_git_command_with_output(symbol: str, file_path: str, 
                                       start_version: str = 'v3.0', end_version: str = 'v6.14',
                                       kernel_path: Optional[str] = None, verbose: bool = False, very_verbose: bool = False, 
                                       max_workers: int = 16, filter_duplicates: bool = False, quiet: bool = False) -> List[str]:
    """Run git command and analyze the output using version range multithreading. Returns output lines instead of printing."""
    output_lines = []
    
    if not quiet:
        output_lines.append(f"{Colors.HEADER}Analyzing {symbol} changes from {start_version} to {end_version}...{Colors.END}")
        if kernel_path:
            output_lines.append(f"{Colors.CYAN}Using kernel source path: {kernel_path}{Colors.END}")
        output_lines.append(f"{Colors.CYAN}Using {max_workers} threads for parallel processing{Colors.END}")
        if filter_duplicates:
            output_lines.append(f"{Colors.CYAN}Filtering duplicate definitions (keeping earliest commit){Colors.END}")
        output_lines.append("=" * 80)
    
    # Divide version range into sub-ranges
    version_ranges = get_version_ranges(start_version, end_version, max_workers, kernel_path)
    
    # Only show version range details in very_verbose mode
    if very_verbose and not quiet:
        output_lines.append(f"{Colors.CYAN}Divided version range into {len(version_ranges)} sub-ranges:{Colors.END}")
        for i, (start_ver, end_ver) in enumerate(version_ranges):
            output_lines.append(f"{Colors.CYAN}  Thread {i+1}: {start_ver}..{end_ver}{Colors.END}")
        output_lines.append("")
    
    # Prepare arguments for thread pool
    thread_args = []
    for i, (start_ver, end_ver) in enumerate(version_ranges):
        thread_args.append((start_ver, end_ver, symbol, file_path, kernel_path, verbose, very_verbose, i + 1, max_workers, quiet))
    
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
                
                # Add progress to output (only in very_verbose mode)
                if very_verbose and not quiet:
                    output_lines.append(f"{Colors.BLUE}Thread {thread_id} completed: {start_ver}..{end_ver} ({len(results)} commits){Colors.END}")
                
            except Exception as e:
                output_lines.append(f"{Colors.RED}Error in thread {thread_id} processing range {start_ver}..{end_ver}: {e}{Colors.END}")
    
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
                if very_verbose and not quiet:
                    output_lines.append(f"{Colors.GREEN}Keeping first occurrence of definition: {normalized_def[:50]}...{Colors.END}")
            else:
                # Duplicate definition found
                original_commit = seen_definitions[normalized_def]['commit_hash']
                current_commit = result['commit_hash']
                if very_verbose and not quiet:
                    output_lines.append(f"{Colors.YELLOW}Filtering duplicate definition in commit {current_commit} (same as {original_commit}){Colors.END}")
        
        all_results = filtered_results
    
    # Add results to output (only in very_verbose mode)
    if very_verbose and not quiet:
        output_lines.append(f"\n{Colors.GREEN}Analysis completed in {time.time() - start_time:.2f} seconds{Colors.END}")
        output_lines.append(f"{Colors.GREEN}Total commits analyzed: {len(all_results)}{Colors.END}")
        if filter_duplicates:
            output_lines.append(f"{Colors.GREEN}Filtered duplicate definitions: {len(seen_definitions) if 'seen_definitions' in locals() else 0} unique definitions{Colors.END}")
        output_lines.append("")
    
    for i, result in enumerate(all_results):
        commit_hash = result['commit_hash']
        thread_id = result.get('thread_id', 'N/A')
        
        if not quiet:
            output_lines.append(f"{Colors.BLUE}Commit {i+1}/{len(all_results)} (Thread {thread_id}): {commit_hash}{Colors.END}")
        
        if result['error']:
            output_lines.append(f"{Colors.RED}Error: {result['error']}{Colors.END}")
            if not quiet:
                output_lines.append("-" * 80)
                output_lines.append("")
            continue
        
        # Add commit info to output
        commit_info = result['commit_info']
        kernel_version = result.get('kernel_version')
        if commit_info and not quiet:
            output_lines.append(f"{Colors.CYAN}Author: {commit_info['author']}{Colors.END}")
            output_lines.append(f"{Colors.CYAN}Date: {commit_info['date']}{Colors.END}")
            if kernel_version:
                output_lines.append(f"{Colors.CYAN}Kernel Version: {kernel_version}{Colors.END}")
            output_lines.append(f"{Colors.CYAN}Message: {commit_info['message']}{Colors.END}")
        
        # Add very verbose information if requested
        if very_verbose and not quiet:
            commit_hash = result['commit_hash']
            
            # Get full commit message
            full_message = get_commit_full_message(commit_hash, kernel_path)
            if full_message:
                output_lines.append("Full commit message:")
                output_lines.append("-" * 40)
                output_lines.append(full_message.strip())
                output_lines.append("-" * 40)
                output_lines.append("")
        
        if result['found']:
            if verbose and result['line_number'] and not quiet:
                output_lines.append(f"{Colors.GREEN}{symbol} definition (line {result['line_number']}):{Colors.END}")
            elif not quiet:
                output_lines.append(f"{Colors.GREEN}{symbol} definition:{Colors.END}")
            
            if quiet:
                # In quiet mode, just show the essential info with colors
                commit_info = result['commit_info']
                if commit_info:
                    version_info = f" [{kernel_version}]" if kernel_version else ""
                    output_lines.append(f"{Colors.BLUE}{commit_hash[:8]}{Colors.END} | {Colors.CYAN}{commit_info['date'][:10]}{version_info}{Colors.END} | {Colors.YELLOW}{commit_info['message']}{Colors.END} | {Colors.GREEN}{result['definition']}{Colors.END}")
            else:
                output_lines.append(f"  {result['definition']}")
                if verbose and result['context']:
                    output_lines.append(f"{Colors.CYAN}  Context:{Colors.END}")
                    output_lines.append(f"  {result['context']}")
        else:
            if not quiet:
                output_lines.append(f"{Colors.RED}  No definition found for {symbol}{Colors.END}")
        
        if not quiet:
            output_lines.append("-" * 80)
            output_lines.append("")
    
    return output_lines

def analyze_from_git_command(symbol: str, file_path: str, 
                           start_version: str = 'v3.0', end_version: str = 'v6.14',
                           kernel_path: Optional[str] = None, verbose: bool = False, very_verbose: bool = False, 
                           max_workers: int = 16, filter_duplicates: bool = False, quiet: bool = False):
    """Run git command and analyze the output using version range multithreading."""
    if not quiet:
        colored_print(f"Analyzing {symbol} changes from {start_version} to {end_version}...", Colors.HEADER, bold=True, quiet=quiet)
        if kernel_path:
            colored_print(f"Using kernel source path: {kernel_path}", Colors.CYAN, quiet=quiet)
        colored_print(f"Using {max_workers} threads for parallel processing", Colors.CYAN, quiet=quiet)
        if filter_duplicates:
            colored_print("Filtering duplicate definitions (keeping earliest commit)", Colors.CYAN, quiet=quiet)
        print("=" * 80)
    
    # Divide version range into sub-ranges
    version_ranges = get_version_ranges(start_version, end_version, max_workers, kernel_path)
    
    # Only show version range details in very_verbose mode
    if very_verbose and not quiet:
        colored_print(f"Divided version range into {len(version_ranges)} sub-ranges:", Colors.CYAN, quiet=quiet)
        for i, (start_ver, end_ver) in enumerate(version_ranges):
            colored_print(f"  Thread {i+1}: {start_ver}..{end_ver}", Colors.CYAN, quiet=quiet)
        print()
    
    # Prepare arguments for thread pool
    thread_args = []
    for i, (start_ver, end_ver) in enumerate(version_ranges):
        thread_args.append((start_ver, end_ver, symbol, file_path, kernel_path, verbose, very_verbose, i + 1, max_workers, quiet))
    
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
                
                # Print progress (only in very_verbose mode)
                if very_verbose and not quiet:
                    colored_print(f"Thread {thread_id} completed: {start_ver}..{end_ver} ({len(results)} commits)", Colors.BLUE, quiet=quiet)
                
            except Exception as e:
                colored_print(f"Error in thread {thread_id} processing range {start_ver}..{end_ver}: {e}", Colors.RED, quiet=quiet)
    
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
                if very_verbose and not quiet:
                    colored_print(f"Keeping first occurrence of definition: {normalized_def[:50]}...", Colors.GREEN, quiet=quiet)
            else:
                # Duplicate definition found
                original_commit = seen_definitions[normalized_def]['commit_hash']
                current_commit = result['commit_hash']
                if very_verbose and not quiet:
                    colored_print(f"Filtering duplicate definition in commit {current_commit} (same as {original_commit})", Colors.YELLOW, quiet=quiet)
        
        all_results = filtered_results
    
    # Print results (only in very_verbose mode)
    if very_verbose and not quiet:
        colored_print(f"\nAnalysis completed in {time.time() - start_time:.2f} seconds", Colors.GREEN, bold=True, quiet=quiet)
        colored_print(f"Total commits analyzed: {len(all_results)}", Colors.GREEN, bold=True, quiet=quiet)
        if filter_duplicates:
            colored_print(f"Filtered duplicate definitions: {len(seen_definitions) if 'seen_definitions' in locals() else 0} unique definitions", Colors.GREEN, bold=True, quiet=quiet)
        print()
    
    for i, result in enumerate(all_results):
        commit_hash = result['commit_hash']
        thread_id = result.get('thread_id', 'N/A')
        
        if not quiet:
            colored_print(f"Commit {i+1}/{len(all_results)} (Thread {thread_id}): {commit_hash}", Colors.BLUE, bold=True)
        
        if result['error']:
            colored_print(f"Error: {result['error']}", Colors.RED, quiet=quiet)
            if not quiet:
                print("-" * 80)
                print()
            continue
        
        # Print commit info
        commit_info = result['commit_info']
        kernel_version = result.get('kernel_version')
        if commit_info and not quiet:
            colored_print(f"Author: {commit_info['author']}", Colors.CYAN)
            colored_print(f"Date: {commit_info['date']}", Colors.CYAN)
            if kernel_version:
                colored_print(f"Kernel Version: {kernel_version}", Colors.CYAN)
            colored_print(f"Message: {commit_info['message']}", Colors.CYAN)
        
        # Print very verbose information if requested
        if very_verbose and not quiet:
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
            if verbose and result['line_number'] and not quiet:
                colored_print(f"{symbol} definition (line {result['line_number']}):", Colors.GREEN, bold=True)
            elif not quiet:
                colored_print(f"{symbol} definition:", Colors.GREEN, bold=True)
            
            if quiet:
                # In quiet mode, just show the essential info with colors
                commit_info = result['commit_info']
                kernel_version = result.get('kernel_version')
                if commit_info:
                    version_info = f" [{kernel_version}]" if kernel_version else ""
                    colored_print(f"{Colors.BLUE}{commit_hash[:8]}{Colors.END} | {Colors.CYAN}{commit_info['date'][:10]}{version_info}{Colors.END} | {Colors.YELLOW}{commit_info['message']}{Colors.END} | {Colors.GREEN}{result['definition']}{Colors.END}")
            else:
                print(f"  {result['definition']}")
                if verbose and result['context']:
                    colored_print("  Context:", Colors.CYAN)
                    print(f"  {result['context']}")
        else:
            if not quiet:
                colored_print(f"  No definition found for {symbol}", Colors.RED)
        
        if not quiet:
            print("-" * 80)
            print()

def analyze_single_symbol(symbol: str, file_path: Optional[str], kernel_path: str, start_version: str, end_version: str, 
                         verbose: bool, very_verbose: bool, threads: int, filter_duplicates: bool, 
                         quiet: bool, symbol_index: int, total_symbols: int) -> str:
    """Analyze a single symbol. This function is designed to be run in a thread."""
    output_lines = []
    
    try:
        if quiet:
            # In quiet mode, show symbol header with color
            output_lines.append(f"{Colors.HEADER}[{symbol_index+1}]{Colors.END} {Colors.BOLD}{symbol}{Colors.END}")
        else:
            output_lines.append(f"\n{Colors.HEADER}Symbol {symbol_index+1}/{total_symbols}: {symbol}{Colors.END}")
            output_lines.append("-" * 60)
        
        # Use provided file path if available, otherwise find it using git grep
        if file_path:
            if not args.quiet:
                colored_print(f"Using provided file path for {symbol}: {file_path}", Colors.GREEN, quiet=args.quiet)
        else:
            file_path = find_symbol_definition_file(symbol, kernel_path)
        
        if file_path:
            # Run git command analysis with the found file path
            symbol_output = analyze_from_git_command_with_output(symbol, file_path, start_version, end_version, 
                                                              kernel_path, verbose, very_verbose, threads, filter_duplicates, quiet)
            output_lines.extend(symbol_output)
        else:
            output_lines.append(f"{Colors.RED}Skipping analysis for {symbol} - definition file not found{Colors.END}")
        
        # Add separator between symbols
        if symbol_index < total_symbols - 1:
            if quiet:
                output_lines.append("")  # Just a blank line in quiet mode
            else:
                output_lines.append("\n" + "=" * 80)
                
    except Exception as e:
        output_lines.append(f"{Colors.RED}Error analyzing symbol {symbol}: {e}{Colors.END}")
    
    return "\n".join(output_lines)

def main():
    """Main entry point."""
    
    # Parse symbols list
    symbols = parse_symbols_list(args.symbol, args.symbols_file)
    
    if not symbols:
        colored_print("Error: No symbols specified. Use --help for usage information.", Colors.RED)
        sys.exit(1)
    
    # Expand user paths
    if args.kernel_path:
        args.kernel_path = os.path.expanduser(args.kernel_path)
    if args.symbols_file:
        args.symbols_file = os.path.expanduser(args.symbols_file)
    
    # Extract symbol names for display
    symbol_names = [symbol for symbol, _ in symbols]
    colored_print(f"Analyzing {len(symbols)} symbol(s): {', '.join(symbol_names)}", Colors.HEADER, bold=True, quiet=args.quiet)
    if not args.quiet:
        print("=" * 80)
    
    try:
        # For single symbol, use the original sequential approach
        if len(symbols) == 1:
            symbol, file_path = symbols[0]
            output = analyze_single_symbol(symbol, file_path, args.kernel_path, args.start_version, args.end_version,
                                         args.verbose, args.very_verbose, args.threads, args.filter_duplicates,
                                         args.quiet, 0, 1)
            print(output)
        else:
            # For multiple symbols, use parallel processing
            # Use min of threads and number of symbols to avoid creating too many threads
            max_workers = min(args.threads, len(symbols))
            if not args.quiet:
                colored_print(f"Using {max_workers} threads for parallel symbol analysis", Colors.CYAN, quiet=args.quiet)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all symbol analysis tasks
                futures = []
                for i, (symbol, file_path) in enumerate(symbols):
                    future = executor.submit(analyze_single_symbol, symbol, file_path, args.kernel_path, 
                                           args.start_version, args.end_version, args.verbose, 
                                           args.very_verbose, args.threads, args.filter_duplicates,
                                           args.quiet, i, len(symbols))
                    futures.append((i, future))
                
                # Collect all outputs and print them in order
                symbol_outputs = []
                for i, future in futures:
                    try:
                        output = future.result()
                        symbol_outputs.append((i, output))
                    except Exception as e:
                        colored_print(f"Error in symbol analysis: {e}", Colors.RED, quiet=args.quiet)
                
                # Print outputs in the original symbol order
                symbol_outputs.sort(key=lambda x: x[0])
                for _, output in symbol_outputs:
                    print(output)
            
    except KeyboardInterrupt:
        colored_print("\nAnalysis interrupted by user", Colors.YELLOW)
    except Exception as e:
        colored_print(f"Error during analysis: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main() 