#!/usr/bin/env python3
"""
Script to extract assembly address ranges from kernel-results/*/*.output.txt files.
Uses debug information from vmlinux to map source line numbers to assembly addresses.

Usage:
    python3 extract_assembly_ranges.py <output.txt file>
    python3 extract_assembly_ranges.py --batch <directory> [--workers N]
    python3 extract_assembly_ranges.py --generate-cache  (regenerate cache files)

The --batch mode processes files in parallel using multiple threads.
Use --workers N to specify the number of parallel workers (default: CPU count).

Output:
    - If "Number of max-level functions:" is not 1, prints "TODO"
    - Otherwise, prints the function name, source locations, and assembly address range
"""

import sys
import re
import subprocess
import os
from pathlib import Path
import glob
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


def get_cache_dir(vmlinux_path):
    """Get the cache directory for a vmlinux file."""
    # Create a unique cache directory based on vmlinux path and modification time
    vmlinux_stat = os.stat(vmlinux_path)
    vmlinux_id = f"{vmlinux_path}_{vmlinux_stat.st_mtime}_{vmlinux_stat.st_size}"
    cache_hash = hashlib.md5(vmlinux_id.encode()).hexdigest()[:16]

    cache_dir = Path(".vmlinux_cache") / cache_hash
    return cache_dir


def generate_nm_cache(vmlinux_path, cache_dir):
    """Generate and cache nm output."""
    print(f"Generating nm cache for {vmlinux_path}...", file=sys.stderr)
    cache_file = cache_dir / "nm_output.txt"
    cache_dir.mkdir(parents=True, exist_ok=True)

    nm_cmd = ['nm', vmlinux_path]
    result = subprocess.run(nm_cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"Error running nm: {result.stderr}", file=sys.stderr)
        return None

    with open(cache_file, 'w') as f:
        f.write(result.stdout)

    print(f"nm cache saved to {cache_file}", file=sys.stderr)
    return result.stdout


def generate_readelf_cache(vmlinux_path, cache_dir):
    """Generate and cache readelf debug line output."""
    print(f"Generating readelf cache for {vmlinux_path} (this may take 2-3 minutes)...", file=sys.stderr)
    cache_file = cache_dir / "readelf_decodedline.txt"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cmd = ['readelf', '--debug-dump=decodedline', vmlinux_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"Error running readelf: {result.stderr}", file=sys.stderr)
        return None

    with open(cache_file, 'w') as f:
        f.write(result.stdout)

    print(f"readelf cache saved to {cache_file}", file=sys.stderr)
    return result.stdout


def load_nm_cache(vmlinux_path, cache_dir):
    """Load cached nm output or generate if not exists."""
    cache_file = cache_dir / "nm_output.txt"

    if cache_file.exists():
        print(f"Loading nm cache from {cache_file}", file=sys.stderr)
        with open(cache_file, 'r') as f:
            return f.read()

    return generate_nm_cache(vmlinux_path, cache_dir)


def load_readelf_cache(vmlinux_path, cache_dir):
    """Load cached readelf output or generate if not exists."""
    cache_file = cache_dir / "readelf_decodedline.txt"

    if cache_file.exists():
        print(f"Loading readelf cache from {cache_file}", file=sys.stderr)
        with open(cache_file, 'r') as f:
            return f.read()

    return generate_readelf_cache(vmlinux_path, cache_dir)


def parse_dataflow_analysis_output_file(filepath):
    """Parse the kernel-results/*/*.output.txt file and extract relevant information."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if "Number of max-level functions:" is 1
    match = re.search(r'Number of max-level functions:\s*(\d+)', content)
    if not match:
        assert False, "Could not find 'Number of max-level functions'"

    num_functions = int(match.group(1))
    if num_functions != 1:
        # Because the current pass output does not have enough information for
        # each span...
        return None, "TODO"

    # Extract function name
    func_match = re.search(r'Function:\s*(\S+)', content)
    if not func_match:
        assert False, "Could not find function name"
    function_name = func_match.group(1)

    # Extract earliest instruction with L=N
    earliest_match = re.search(
        r'Earliest instruction with L=\d+:\s*\n\s*.*?<([^>]+)>\s+FUNC=(\S+)',
        content,
        re.MULTILINE
    )

    # Extract latest instruction with L=0
    latest_match = re.search(
        r'Latest instruction with L=\d+:\s*\n\s*.*?<([^>]+)>\s+FUNC=(\S+)',
        content,
        re.MULTILINE
    )

    # Check if earliest and latest are the same
    same_instruction = "(Earliest and latest are the same instruction)" in content

    if not earliest_match:
        # IR instruction without source code location
        earliest_match = re.search(
            r'Earliest instruction with L=\d+:\s*\n\s*(.*?)\s+FUNC=(\S+)',
            content,
            re.MULTILINE
        )
        assert earliest_match is not None
        # Example without source code location:
        #   %46 = phi i64 [ 0, %40 ], [ 60000, %32 ]
        # Example with source code location:
        #   %47 = load ptr, ptr @amt_wq, align 8, !dbg !23706890
        # Let's maybe approximate by looking forward/backward a few
        # instructions in our pass.
        # print(f"[TODO] Start IR instruction without source code location")
        # print(f"  File: {filepath}")
        # print(f"  Earliest instruction: {earliest_match.group(1)}")
        # print(f"  Function: {earliest_match.group(2)}")
        return None, "The start IR instruction does not have corresponding source code location"

    earliest_location = earliest_match.group(1)
    earliest_func = earliest_match.group(2)

    if same_instruction:
        latest_location = earliest_location
        latest_func = earliest_func
    else:
        if not latest_match:
            # IR instruction without source code location
            latest_match = re.search(
                r'Latest instruction with L=\d+:\s*\n\s*(.*?)\s+FUNC=(\S+)',
                content,
                re.MULTILINE
            )
            assert latest_match is not None
            # print(f"[TODO] End IR instruction without source code location")
            # print(f"  File: {filepath}")
            # print(f"  Latest instruction: {latest_match.group(1)}")
            # print(f"  Function: {latest_match.group(2)}")
            return None, "The end IR instruction does not have corresponding source code location"
        latest_location = latest_match.group(1)
        latest_func = latest_match.group(2)

    # Parse source locations (format: file:line:column)
    def parse_location(loc):
        parts = loc.rsplit(':', 2)
        if len(parts) >= 2:
            return parts[0], int(parts[1])
        return None, None

    earliest_file, earliest_line = parse_location(earliest_location)
    latest_file, latest_line = parse_location(latest_location)

    if not earliest_file or not earliest_line:
        # print(f"[TODO] Could not parse source code location: {earliest_location}")
        # print(f"  File: {filepath}")
        # print(f"  Location: {earliest_location}")
        # print(f"  Function: {earliest_match.group(2)}")
        return None, f"Could not parse earliest location: {earliest_location}"

    if not latest_file or not latest_line:
        # print(f"[TODO] Could not parse source code location: {latest_location}")
        # print(f"  File: {filepath}")
        # print(f"  Location: {latest_location}")
        # print(f"  Function: {latest_match.group(2)}")
        return None, f"Could not parse latest location: {latest_location}"

    return {
        'function': function_name,
        'earliest_func': earliest_func,
        'latest_func': latest_func,
        'earliest_file': earliest_file,
        'earliest_line': earliest_line,
        'latest_file': latest_file,
        'latest_line': latest_line,
    }, None


def normalize_path(path):
    """Normalize source file path for matching."""
    # Remove leading ./ or ../
    path = path.lstrip('./')
    # FIXME I don't think this is needed
    # # Handle relative paths like ../linux-wllvm-defconfig/
    # if path.startswith('../'):
    #     # Extract just the file path after the project directory
    #     parts = path.split('/')
    #     # Find where the actual source path starts (after project directories)
    #     for i, part in enumerate(parts):
    #         if part in ['fs', 'drivers', 'include', 'kernel', 'mm', 'net', 'arch', 'lib']:
    #             return '/'.join(parts[i:])
    return path


def find_address_for_line_using_readelf(readelf_output, source_file, line_number):
    """
    Use readelf output to search debug line information for a specific source line.
    This is a fallback when the function is not in the symbol table.
    """
    try:
        if not readelf_output:
            return None

        normalized_source = normalize_path(source_file)
        # Extract just the filename for matching
        source_filename = os.path.basename(source_file)
        addresses = []

        # Parse readelf output
        # Format has directory headers like "kernel/cgroup/workqueue.h:"
        # followed by lines like "workqueue.h  692  0xffffffff814c7791"
        current_dir = None
        for line in readelf_output.splitlines():
            # Check if this is a directory/file path header
            if line.endswith(':') and '/' in line:
                current_dir = line.rstrip(':')
            elif source_filename in line:
                # Parse lines like "workqueue.h  692  0xffffffff814c7791"
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        file_name = parts[0]
                        line_num = int(parts[1])
                        # Look for address in the remaining parts
                        for part in parts[2:]:
                            if part.startswith('0x'):
                                addr = part[2:]
                                # Check if this matches our target line
                                if line_num == line_number and file_name == source_filename:
                                    # Verify the directory path if available
                                    # FIXME
                                    if current_dir:
                                        full_path = normalize_path(current_dir)
                                        # Check if paths are compatible
                                        if normalized_source in full_path or source_filename in current_dir:
                                            addresses.append(addr)
                                            break
                                    else:
                                        addresses.append(addr)
                                        break
                    except (ValueError, IndexError):
                        continue

        if addresses:
            return addresses[0]

        return None

    except Exception as e:
        print(f"Readelf exception: {e}", file=sys.stderr)
        return None


def find_address_for_line(vmlinux_path, nm_output, readelf_output, source_file, line_number, function_name):
    """
    Use objdump to find the assembly address for a given source line.
    Returns the address or None if not found.
    """
    try:
        if not nm_output:
            return None

        # Get symbol address for the function using nm
        func_addr = None
        for line in nm_output.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                symbol_name = parts[2]
                # Match exact function name or with .llvm suffix # FIXME
                if symbol_name == function_name or symbol_name.startswith(f"{function_name}."):
                    func_addr = parts[0]
                    break

        if not func_addr:
            print(f"Warning: Could not find function '{function_name}' in symbol table, trying readelf fallback", file=sys.stderr)
            # Try fallback method using readelf
            addr = find_address_for_line_using_readelf(readelf_output, source_file, line_number)
            if addr:
                print(f"Found address using readelf fallback", file=sys.stderr)
            return addr

        # Use objdump to disassemble the function with source line info
        # -d: disassemble, -l: include line numbers, -S: intermix source code
        objdump_cmd = [
            'objdump', '-d', '-l', '-S',
            '--start-address=0x' + func_addr,
            '--stop-address=0x' + hex(int(func_addr, 16) + 0x100000)[2:],
            vmlinux_path
        ]
        objdump_result = subprocess.run(objdump_cmd, capture_output=True, text=True, timeout=600)

        # Parse objdump output to find addresses matching the source line
        addresses = []
        normalized_source = normalize_path(source_file)

        current_addr = None
        current_file = None
        current_line = None

        for line in objdump_result.stdout.splitlines():
            # Match source file/line references like "/path/to/file.c:123"
            src_match = re.match(r'^([^:]+):(\d+)', line)
            if src_match:
                current_file = src_match.group(1)
                current_line = int(src_match.group(2))
                continue

            # Match address lines like "ffffffff81234567:"
            addr_match = re.match(r'^\s*([0-9a-f]+):\s+', line)
            if addr_match:
                current_addr = addr_match.group(1)

                # Check if this address corresponds to our target line
                if current_file and current_line:
                    # Normalize the file path for comparison
                    norm_current = normalize_path(current_file)
                    if norm_current.endswith(normalized_source) or normalized_source.endswith(norm_current):
                        if current_line == line_number:
                            addresses.append(current_addr)

        if addresses:
            return addresses[0]  # Return the first matching address

        # If no exact match, try readelf fallback
        print(f"Warning: No exact match found in objdump for {normalized_source}:{line_number}, trying readelf", file=sys.stderr)
        addr = find_address_for_line_using_readelf(readelf_output, source_file, line_number)
        if addr:
            print(f"Found address using readelf fallback", file=sys.stderr)
        return addr

    except subprocess.TimeoutExpired:
        print(f"Error: Timeout while processing {vmlinux_path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error finding address: {e}", file=sys.stderr)
        return None


def process_single_file(output_file, vmlinux_path, nm_output, readelf_output, verbose=True):
    """Process a single output file and return the results."""
    if not os.path.exists(output_file):
        if verbose:
            print(f"Error: File {output_file} not found")
        return None

    # Parse the output file
    result, error = parse_dataflow_analysis_output_file(output_file)

    if error:
        if error == "TODO":
            if verbose:
                print("TODO")
            return {"status": "TODO", "file": output_file}
        else:
            if verbose:
                print(f"Error: {error}")
            return {"status": "ERROR", "file": output_file, "error": error}

    # Find assembly addresses
    if verbose:
        print(f"Function: {result['function']}")
        print(f"Earliest: {result['earliest_file']}:{result['earliest_line']} (in {result['earliest_func']})")
        print(f"Latest: {result['latest_file']}:{result['latest_line']} (in {result['latest_func']})")
        print()

    earliest_addr = find_address_for_line(
        vmlinux_path,
        nm_output,
        readelf_output,
        result['earliest_file'],
        result['earliest_line'],
        result['earliest_func']
    )

    latest_addr = find_address_for_line(
        vmlinux_path,
        nm_output,
        readelf_output,
        result['latest_file'],
        result['latest_line'],
        result['latest_func']
    )

    if verbose:
        if earliest_addr and latest_addr:
            print(f"Assembly address range: 0x{earliest_addr} - 0x{latest_addr}")
        elif earliest_addr:
            print(f"Start address: 0x{earliest_addr}")
            print("End address: Not found")
        elif latest_addr:
            print(f"Start address: Not found")
            print(f"End address: 0x{latest_addr}")
        else:
            print("Assembly addresses: Not found")
            print(f"(Tried to find addresses for {result['earliest_func']} in {vmlinux_path})")

    return {
        "status": "SUCCESS",
        "file": output_file,
        "function": result['function'],
        "earliest_file": result['earliest_file'],
        "earliest_line": result['earliest_line'],
        "latest_file": result['latest_file'],
        "latest_line": result['latest_line'],
        "start_addr": earliest_addr,
        "end_addr": latest_addr
    }


def batch_process(directory, vmlinux_path, nm_output, readelf_output, max_workers=None):
    """Process all .output.txt files in a directory tree in parallel."""
    pattern = os.path.join(directory, '**', '*.output.txt')
    files = glob.glob(pattern, recursive=True)

    if not files:
        print(f"No .output.txt files found in {directory}")
        return

    print(f"Processing {len(files)} files in parallel...")
    print()

    results = {"TODO": [], "SUCCESS": [], "ERROR": [], "NOT_FOUND": []}
    completed_count = 0
    print_lock = threading.Lock()

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, file_path, vmlinux_path, nm_output, readelf_output, False): file_path
            for file_path in sorted(files)
        }

        # Process results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()

                with print_lock:
                    completed_count += 1
                    print(f"[{completed_count}/{len(files)}] {file_path}")

                    if result:
                        if result["status"] == "TODO":
                            results["TODO"].append(file_path)
                            print("  -> TODO")
                        elif result["status"] == "ERROR":
                            results["ERROR"].append((file_path, result.get("error", "Unknown error")))
                            print(f"  -> ERROR: {result.get('error', 'Unknown')}")
                        elif result["status"] == "SUCCESS":
                            if result["start_addr"] and result["end_addr"]:
                                results["SUCCESS"].append((file_path, result["start_addr"], result["end_addr"]))
                                print(f"  -> 0x{result['start_addr']} - 0x{result['end_addr']}")
                            else:
                                results["NOT_FOUND"].append(file_path)
                                print(f"  -> Addresses not found")
                    print()
            except Exception as e:
                with print_lock:
                    completed_count += 1
                    print(f"[{completed_count}/{len(files)}] {file_path}")
                    print(f"  -> EXCEPTION: {e}")
                    results["ERROR"].append((file_path, str(e)))
                    print()

    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files: {len(files)}")
    print(f"TODO (multiple max-level functions): {len(results['TODO'])}")
    print(f"SUCCESS (addresses found): {len(results['SUCCESS'])}")
    print(f"NOT_FOUND (addresses not found): {len(results['NOT_FOUND'])}")
    print(f"ERROR: {len(results['ERROR'])}")


def main():
    # vmlinux_path = "../addr/linux-6.14.0/vmlinux"
    vmlinux_path = "./xkernel.vmlinux"

    if not os.path.exists(vmlinux_path):
        print(f"Error: vmlinux file {vmlinux_path} not found")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 extract_assembly_ranges.py <output_file>")
        print("       python3 extract_assembly_ranges.py --batch <directory> [--workers N]")
        print("       python3 extract_assembly_ranges.py --generate-cache")
        sys.exit(1)

    # Get cache directory
    cache_dir = get_cache_dir(vmlinux_path)

    # Handle cache generation
    if sys.argv[1] == "--generate-cache":
        print(f"Generating cache for {vmlinux_path}")
        print(f"Cache directory: {cache_dir}")
        generate_nm_cache(vmlinux_path, cache_dir)
        generate_readelf_cache(vmlinux_path, cache_dir)
        print("Cache generation complete!")
        sys.exit(0)

    # Load caches
    nm_output = load_nm_cache(vmlinux_path, cache_dir)
    readelf_output = load_readelf_cache(vmlinux_path, cache_dir)

    if not nm_output:
        print("Error: Failed to load nm cache", file=sys.stderr)
        sys.exit(1)

    if not readelf_output:
        print("Error: Failed to load readelf cache", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Usage: python3 extract_assembly_ranges.py --batch <directory> [--workers N]")
            sys.exit(1)

        directory = sys.argv[2]
        max_workers = None

        # Check for optional --workers argument
        if len(sys.argv) >= 5 and sys.argv[3] == "--workers":
            try:
                max_workers = int(sys.argv[4])
                print(f"Using {max_workers} parallel workers")
            except ValueError:
                print("Error: --workers argument must be an integer")
                sys.exit(1)

        batch_process(directory, vmlinux_path, nm_output, readelf_output, max_workers)
    else:
        output_file = sys.argv[1]
        process_single_file(output_file, vmlinux_path, nm_output, readelf_output, verbose=True)


if __name__ == '__main__':
    main()

