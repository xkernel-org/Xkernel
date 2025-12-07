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


def build_symbol_to_module_map(module_nm_cache, module_files):
    """
    Build a mapping from symbol names to module names by parsing nm output from all modules.
    This is more reliable than Module.symvers which only contains exported symbols.
    Returns a dict: {symbol_name: (module_name, ko_path)}
    """
    symbol_to_module = {}

    print(f"Building symbol-to-module mapping from nm output...", file=sys.stderr)

    for module_name, nm_output in module_nm_cache.items():
        if module_name not in module_files:
            continue

        ko_path = module_files[module_name]

        # Parse nm output to extract symbols
        for line in nm_output.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                # nm format: <address> <type> <symbol>
                symbol_name = parts[2]
                # Store the module name and path for this symbol
                # If symbol exists in multiple modules, last one wins (could track all if needed)
                symbol_to_module[symbol_name] = (module_name, ko_path)

    print(f"Built mapping for {len(symbol_to_module)} symbols across {len(module_nm_cache)} modules", file=sys.stderr)
    return symbol_to_module


def find_module_files(modules_dir):
    """
    Scan the modules directory and create a mapping from module names to .ko file paths.
    Returns a dict: {module_name: ko_file_path}
    """
    module_files = {}

    if not os.path.exists(modules_dir):
        print(f"Warning: Modules directory not found at {modules_dir}", file=sys.stderr)
        return module_files

    print(f"Scanning for kernel modules in {modules_dir}...", file=sys.stderr)

    # Find all .ko files recursively
    for ko_file in Path(modules_dir).rglob("*.ko"):
        # Extract module name from filename (without .ko extension)
        module_name = ko_file.stem
        module_files[module_name] = str(ko_file)

    print(f"Found {len(module_files)} kernel module files", file=sys.stderr)
    return module_files


def get_module_cache_dir(ko_path):
    """Get the cache directory for a kernel module file."""
    ko_stat = os.stat(ko_path)
    ko_id = f"{ko_path}_{ko_stat.st_mtime}_{ko_stat.st_size}"
    cache_hash = hashlib.md5(ko_id.encode()).hexdigest()[:16]

    cache_dir = Path(".module_cache") / cache_hash
    return cache_dir


def load_module_caches(module_files):
    """
    Load nm and readelf caches for all kernel modules.
    Returns two dicts: {module_name: nm_output}, {module_name: readelf_output}
    """
    module_nm_cache = {}
    module_readelf_cache = {}

    print(f"Loading caches for {len(module_files)} modules...", file=sys.stderr)

    for module_name, ko_path in module_files.items():
        cache_dir = get_module_cache_dir(ko_path)

        # Load nm cache
        nm_output = load_nm_cache(ko_path, cache_dir)
        if nm_output:
            module_nm_cache[module_name] = nm_output

        # Load readelf cache
        readelf_output = load_readelf_cache(ko_path, cache_dir)
        if readelf_output:
            module_readelf_cache[module_name] = readelf_output

    print(f"Loaded caches for {len(module_nm_cache)} modules", file=sys.stderr)
    return module_nm_cache, module_readelf_cache


def find_symbol_binary(function_name, symbol_to_module):
    """
    Determine which binary (vmlinux or a module) contains the function.
    Returns tuple: (binary_path, binary_type, module_name)
    where binary_type is 'vmlinux' or 'module'

    symbol_to_module format: {symbol_name: (module_name, ko_path)}
    """
    # Check if symbol is in a module
    if function_name in symbol_to_module:
        module_name, ko_path = symbol_to_module[function_name]
        return ko_path, 'module', module_name

    if f"{function_name}.part.0" in symbol_to_module:
        module_name, ko_path = symbol_to_module[f"{function_name}.part.0"]
        return ko_path, 'module', module_name

    if f"{function_name}.isra.0" in symbol_to_module:
        module_name, ko_path = symbol_to_module[f"{function_name}.isra.0"]
        return ko_path, 'module', module_name

    # Default to vmlinux
    return None, 'vmlinux', None


def parse_dataflow_analysis_output_file(filepath):
    """Parse the kernel-results/*/*.output.txt file and extract relevant information."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Manual tweaks
    if filepath == "kernel-results/BLK_PLUG_FLUSH_SIZE/1.output.txt":
        # Multiline predicate
        # https://elixir.bootlin.com/linux/v6.14/source/block/blk-mq.c#L1383
        content = content.replace(
            "%44 = icmp ugt i32 %43, 131071, <block/blk-mq.c:1383:26>",
            "%44 = icmp ugt i32 %43, 131071, <block/blk-mq.c:1382:26>"
        )
        content = content.replace(
            "br i1 %44, label %45, label %67, <block/blk-mq.c:1381:59>",
            "br i1 %44, label %45, label %67, <block/blk-mq.c:1382:59>"
        )
    if filepath == "kernel-results/GSSD_MIN_TIMEOUT/1.output.txt":
        # Function inlining
        content = content.replace(
            "gss_fill_context",
            "gss_pipe_downcall"
        )
    if filepath == "kernel-results/IPVS_SYNC_WAKEUP_RATE/1.output.txt":
        # Function inlining
        content = content.replace(
            "sb_queue_tail",
            "ip_vs_sync_conn"
        )
    if filepath == "kernel-results/IPVS_SYNC_WAKEUP_RATE/2.output.txt":
        # Multiline predicate
        # https://elixir.bootlin.com/linux/v6.14/source/net/netfilter/ipvs/ip_vs_sync.c#L1627
        content = content.replace(
            "%12 = icmp ult i32 %11, 8, <net/netfilter/ipvs/ip_vs_sync.c:1628:27>",
            "%12 = icmp ult i32 %11, 8, <net/netfilter/ipvs/ip_vs_sync.c:1627:27>"
        )
    if filepath == "kernel-results/MAX_MKSPC_RETRIES/1.output.txt" or \
       filepath == "kernel-results/NR_TO_WRITE/1.output.txt":
        # Function inlining
        content = content.replace(
            "make_free_space",
            "ubifs_budget_space"
        )
    if filepath == "kernel-results/DEF_PRIORITY/7.output.txt":
        # Multiline predicate
        # https://elixir.bootlin.com/linux/v6.14/source/mm/vmscan.c#L5824
        content = content.replace(
            "<mm/vmscan.c:5826:18>",
            "<mm/vmscan.c:5825:18>"
        )
        content = content.replace(
            "<mm/vmscan.c:5824:56>",
            "<mm/vmscan.c:5825:56>"
        )
    if filepath == "kernel-results/NFS_JUKEBOX_RETRY_TIME/18.output.txt":
        # FIXME inlined in multiple places...
        content = content.replace(
            "nfs3_do_create",
            # "nfs3_proc_create"
            # "nfs3_proc_symlink"
            # "nfs3_proc_mkdir"
            "nfs3_proc_mknod"
        )
        # Inlined <- macro <- inline in multiple places...
        # https://elixir.bootlin.com/linux/v6.14/source/fs/nfs/nfs3proc.c#L320
        content = content.replace(
            "<fs/nfs/nfs3proc.c:40:",
            "<fs/nfs/nfs3proc.c:320:"
        )
    if filepath == "kernel-results/MAX_NR_FOLIOS_PER_FREE/2.output.txt":
        # This time IR inlines more aggressively?
        content = content.replace(
            "tlb_flush_mmu",
            "__tlb_batch_free_encoded_pages"
        )
        # Multiline predicate
        # https://elixir.bootlin.com/linux/v6.14/source/mm/mmu_gather.c#L126
        content = content.replace(
            "<mm/mmu_gather.c:125:",
            "<mm/mmu_gather.c:126:"
        )
    if filepath == "kernel-results/TCP_DELACK_MIN/1.output.txt":
        # Multiline statement
        # https://elixir.bootlin.com/linux/v6.14/source/net/dccp/timer.c#L181
        content = content.replace(
            "<net/dccp/timer.c:181:",
            "<net/dccp/timer.c:180:"
        )
    elif filepath == "kernel-results/bfq_late_stable_merging/1.output.txt":
        content = content.replace(
            "<block/bfq-iosched.c:2951:",
            "<block/bfq-iosched.c:2950:"
        )
    elif filepath == "kernel-results/bfq_late_stable_merging/2.output.txt":
        # Reordered
        content = content.replace(
            "<block/bfq-iosched.c:2952:",
            "<block/bfq-iosched.c:2950:"
        )
        content = content.replace(
            "<block/bfq-iosched.c:2951:",
            "<block/bfq-iosched.c:2952:"
        )
    elif filepath == "kernel-results/bfq_stats_min_budgets/4.output.txt":
        # Crazy inlining
        content = content.replace(
            "bfq_add_request",
            "bfq_insert_requests"
        )
        # bfq_min_budget -> bfq_bfqq_expire
        #                -> bfq_insert_requests
    elif filepath == "kernel-results/max_service_from_wr/1.output.txt":
        content = content.replace(
            "<block/bfq-iosched.c:5095:",
            "<block/bfq-iosched.c:5094:"
        )
    elif filepath == "kernel-results/TCP_THIN_LINEAR_RETRIES/1.output.txt":
        content = content.replace(
            "<net/ipv4/tcp_timer.c:664:",
            "<net/ipv4/tcp_timer.c:663:"
        )
    elif filepath == "kernel-results/TCP_MAX_WSCALE/2.output.txt":
        content = content.replace(
            "<net/core/filter.c:12019:",
            "<net/core/filter.c:12018:"
        )

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

    # Extract latest instruction with L=N
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


def find_address_range_for_single_line(binary_path, nm_output, readelf_output, source_file, line_number, function_name, symbol_to_module=None, module_nm_cache=None, module_readelf_cache=None):
    """
    Find all assembly instructions that correspond to a single source line.
    Returns a tuple of (start_addr, end_addr, base_address, symbol_name) or (None, None, None, None) if not found.
    This is used when the start and end source locations are the same line.

    With the below example, previously we would return [b124, b124].
    Now we will return [b124, b2e1].

    /users/user42/linux-6.14.0-xkernel/io_uring/napi.c:170
    ffffffff81afb124:	41 8b 3f             	mov    (%r15),%edi
    ffffffff81afb127:	4c 89 ea             	mov    %r13,%rdx
    ffffffff81afb12a:	83 e1 01             	and    $0x1,%ecx
    ffffffff81afb12d:	41 b8 08 00 00 00    	mov    $0x8,%r8d
    ffffffff81afb133:	4c 89 e6             	mov    %r12,%rsi
    ffffffff81afb136:	e8 65 72 6c 00       	call   ffffffff821c23a0 <napi_busy_loop_rcu>
    /users/user42/linux-6.14.0-xkernel/io_uring/napi.c:169 (discriminator 5)
    ...
    /users/user42/linux-6.14.0-xkernel/io_uring/napi.c:170
    ffffffff81afb2d0:	41 8b 3c 24          	mov    (%r12),%edi
    ffffffff81afb2d4:	83 e1 01             	and    $0x1,%ecx
    ffffffff81afb2d7:	41 b8 08 00 00 00    	mov    $0x8,%r8d
    ffffffff81afb2dd:	31 d2                	xor    %edx,%edx
    ffffffff81afb2df:	31 f6                	xor    %esi,%esi
    ffffffff81afb2e1:	e8 ba 70 6c 00       	call   ffffffff821c23a0 <napi_busy_loop_rcu>
    /users/user42/linux-6.14.0-xkernel/io_uring/napi.c:169 (discriminator 5)

    """
    try:
        # Check if function is in a module
        actual_binary = binary_path
        actual_nm = nm_output
        actual_readelf = readelf_output

        if symbol_to_module and module_nm_cache:
            module_binary, binary_type, module_name = find_symbol_binary(function_name, symbol_to_module)
            if binary_type == 'module' and module_binary:
                actual_binary = module_binary
                actual_nm = module_nm_cache.get(module_name, nm_output)
                actual_readelf = module_readelf_cache.get(module_name, readelf_output) if module_readelf_cache else readelf_output
                print(f"Using module {module_name} for function {function_name}", file=sys.stderr)

        if not actual_nm:
            return None, None, None, None

        # Get symbol address for the function using nm
        func_addr = None
        func_symbol = None
        for line in actual_nm.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                symbol_name = parts[2]
                # Match exact function name or with suffixes
                if symbol_name == function_name or symbol_name.startswith(f"{function_name}."):
                    if symbol_name.startswith(f"{function_name}."):
                        print(f"FINDME: Picked up a symbol name that's not an exact match {symbol_name}", file=sys.stderr)
                    func_addr = parts[0]
                    func_symbol = symbol_name
                    break

        if not func_addr:
            print(f"Warning: Could not find function '{function_name}' in symbol table for range finding", file=sys.stderr)
            # Try fallback - just find single address
            addr = find_address_for_line_using_readelf(actual_readelf, source_file, line_number)
            if addr:
                print(f"TODO: Found single address using readelf fallback for a single source line (function: {function_name}, source file: {source_file}, line number: {line_number})", file=sys.stderr)
                return addr, addr, None, function_name
            print(f"TODO: No address found for function: {function_name}, source file: {source_file}, line number: {line_number}", file=sys.stderr)
            return None, None, None, None

        # Use objdump to disassemble the function with source line info
        objdump_cmd = [
            'objdump', '-d', '-l', '-S',
            '--start-address=0x' + func_addr,
            '--stop-address=0x' + hex(int(func_addr, 16) + 0x100000)[2:],
            actual_binary
        ]
        print(f"objdump_cmd: {' '.join(objdump_cmd)}")
        objdump_result = subprocess.run(objdump_cmd, capture_output=True, text=True, timeout=600)

        # Parse objdump output to find ALL addresses matching the source line
        addresses = []
        normalized_source = normalize_path(source_file)

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
            # Return the range: first instruction to last instruction
            start_addr = addresses[0]
            end_addr = addresses[-1]
            return start_addr, end_addr, func_addr, func_symbol

        # If no exact match, try readelf fallback
        print(f"Warning: No match found in objdump for {normalized_source}:{line_number}, trying readelf", file=sys.stderr)
        addr = find_address_for_line_using_readelf(actual_readelf, source_file, line_number)
        if addr:
            print(f"TODO: Found single address using readelf fallback for a single source line (function: {function_name}, source file: {source_file}, line number: {line_number})", file=sys.stderr)
            return addr, addr, func_addr, func_symbol
        return None, None, None, None

    except subprocess.TimeoutExpired:
        print(f"Error: Timeout while processing {actual_binary}", file=sys.stderr)
        return None, None, None, None
    except Exception as e:
        print(f"Error finding address range: {e}", file=sys.stderr)
        return None, None, None, None


def find_address_for_line(binary_path, nm_output, readelf_output, source_file, line_number, function_name, symbol_to_module=None, module_nm_cache=None, module_readelf_cache=None):
    """
    Use objdump to find the assembly address for a given source line.
    Returns a tuple of (address, base_address, symbol_name) or (None, None, None) if not found.
    """
    try:
        # Check if function is in a module
        actual_binary = binary_path
        actual_nm = nm_output
        actual_readelf = readelf_output

        if symbol_to_module and module_nm_cache:
            module_binary, binary_type, module_name = find_symbol_binary(function_name, symbol_to_module)
            if binary_type == 'module' and module_binary:
                actual_binary = module_binary
                actual_nm = module_nm_cache.get(module_name, nm_output)
                actual_readelf = module_readelf_cache.get(module_name, readelf_output) if module_readelf_cache else readelf_output
                print(f"Using module {module_name} for function {function_name}", file=sys.stderr)

        if not actual_nm:
            return None, None, None

        # Get symbol address for the function using nm
        func_addr = None
        func_symbol = None
        for line in actual_nm.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                symbol_name = parts[2]
                # Match exact function name or with suffixes
                if symbol_name == function_name or symbol_name.startswith(f"{function_name}."):
                    if symbol_name.startswith(f"{function_name}."):
                        print(f"FINDME: Picked up a symbol name that's not an exact match {symbol_name}", file=sys.stderr)
                    func_addr = parts[0]
                    func_symbol = symbol_name
                    break

        if not func_addr:
            print(f"Warning: Could not find function '{function_name}' in symbol table, trying readelf fallback", file=sys.stderr)
            # Try fallback method using readelf
            addr = find_address_for_line_using_readelf(actual_readelf, source_file, line_number)
            if addr:
                print(f"Found address using readelf fallback", file=sys.stderr)
            return (addr, None, function_name) if addr else (None, None, None)

        # Use objdump to disassemble the function with source line info
        # -d: disassemble, -l: include line numbers, -S: intermix source code
        objdump_cmd = [
            'objdump', '-d', '-l', '-S',
            '--start-address=0x' + func_addr,
            '--stop-address=0x' + hex(int(func_addr, 16) + 0x100000)[2:],
            actual_binary
        ]
        print(f"objdump_cmd: {' '.join(objdump_cmd)}")

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
            return addresses[0], func_addr, func_symbol  # Return address, base address, and symbol name

        # If no exact match, try readelf fallback
        print(f"Warning: No exact match found in objdump for {normalized_source}:{line_number}, trying readelf", file=sys.stderr)
        addr = find_address_for_line_using_readelf(actual_readelf, source_file, line_number)
        if addr:
            print(f"Found address using readelf fallback", file=sys.stderr)
            return addr, func_addr, func_symbol
        return None, None, None

    except subprocess.TimeoutExpired:
        print(f"Error: Timeout while processing {actual_binary}", file=sys.stderr)
        return None, None, None
    except Exception as e:
        print(f"Error finding address: {e}", file=sys.stderr)
        return None, None, None


def process_single_file(output_file, vmlinux_path, nm_output, readelf_output, verbose=True, symbol_to_module=None, module_nm_cache=None, module_readelf_cache=None):
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

    # Check if start and end are the same source location
    if (result['earliest_file'] == result['latest_file'] and
        result['earliest_line'] == result['latest_line'] and
        result['earliest_func'] == result['latest_func']):
        # Same source line - find the assembly range for this single line
        earliest_addr, latest_addr, earliest_base, earliest_symbol = find_address_range_for_single_line(
            vmlinux_path,
            nm_output,
            readelf_output,
            result['earliest_file'],
            result['earliest_line'],
            result['earliest_func'],
            symbol_to_module,
            module_nm_cache,
            module_readelf_cache
        )
        latest_base = earliest_base
        latest_symbol = earliest_symbol
    else:
        # Different source locations - find each address separately
        earliest_addr, earliest_base, earliest_symbol = find_address_for_line(
            vmlinux_path,
            nm_output,
            readelf_output,
            result['earliest_file'],
            result['earliest_line'],
            result['earliest_func'],
            symbol_to_module,
            module_nm_cache,
            module_readelf_cache
        )

        latest_addr, latest_base, latest_symbol = find_address_for_line(
            vmlinux_path,
            nm_output,
            readelf_output,
            result['latest_file'],
            result['latest_line'],
            result['latest_func'],
            symbol_to_module,
            module_nm_cache,
            module_readelf_cache
        )

    # Calculate offsets if we have base addresses
    earliest_offset = None
    latest_offset = None
    if earliest_addr and earliest_base:
        earliest_offset = hex(int(earliest_addr, 16) - int(earliest_base, 16))
    if latest_addr and latest_base:
        latest_offset = hex(int(latest_addr, 16) - int(latest_base, 16))

    if verbose:
        if earliest_addr and latest_addr:
            # Format: source start, source end, binary start, binary end, symbol name, start offset, end offset
            source_start = f"{result['earliest_file']}:{result['earliest_line']}"
            source_end = f"{result['latest_file']}:{result['latest_line']}"
            binary_start = f"0x{earliest_addr}"
            binary_end = f"0x{latest_addr}"
            symbol = earliest_symbol if earliest_symbol else "N/A"
            start_off = earliest_offset if earliest_offset else "N/A"
            end_off = latest_offset if latest_offset else "N/A"

            print(f"{source_start}, {source_end}, {binary_start}, {binary_end}, {symbol}, {start_off}, {end_off}")
        elif earliest_addr:
            source_start = f"{result['earliest_file']}:{result['earliest_line']}"
            binary_start = f"0x{earliest_addr}"
            symbol = earliest_symbol if earliest_symbol else "N/A"
            start_off = earliest_offset if earliest_offset else "N/A"
            print(f"{source_start}, N/A, {binary_start}, N/A, {symbol}, {start_off}, N/A")
        elif latest_addr:
            source_end = f"{result['latest_file']}:{result['latest_line']}"
            binary_end = f"0x{latest_addr}"
            symbol = latest_symbol if latest_symbol else "N/A"
            end_off = latest_offset if latest_offset else "N/A"
            print(f"N/A, {source_end}, N/A, {binary_end}, {symbol}, N/A, {end_off}")
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
        "end_addr": latest_addr,
        "start_symbol": earliest_symbol,
        "end_symbol": latest_symbol,
        "start_offset": earliest_offset,
        "end_offset": latest_offset
    }


def batch_process(directory, vmlinux_path, nm_output, readelf_output, max_workers=None, symbol_to_module=None, module_nm_cache=None, module_readelf_cache=None):
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

    # Open output file for writing results
    output_log_path = "addr.log"
    output_file = open(output_log_path, 'w')
    print(f"Saving results to {output_log_path}", file=sys.stderr)
    print()

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, file_path, vmlinux_path, nm_output, readelf_output, False,
                          symbol_to_module, module_nm_cache, module_readelf_cache): file_path
            for file_path in sorted(files)
        }

        # Process results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()

                with print_lock:
                    completed_count += 1
                    header_line = f"[{completed_count}/{len(files)}] {file_path}"
                    print(header_line)
                    output_file.write(header_line + "\n")

                    if result:
                        if result["status"] == "TODO":
                            results["TODO"].append(file_path)
                            result_line = "  -> TODO"
                            print(result_line)
                            output_file.write(result_line + "\n")
                        elif result["status"] == "ERROR":
                            results["ERROR"].append((file_path, result.get("error", "Unknown error")))
                            result_line = f"  -> ERROR: {result.get('error', 'Unknown')}"
                            print(result_line)
                            output_file.write(result_line + "\n")
                        elif result["status"] == "SUCCESS":
                            if result["start_addr"] and result["end_addr"]:
                                # Format: source start, source end, binary start, binary end, symbol name, start offset, end offset
                                source_start = f"{result['earliest_file']}:{result['earliest_line']}"
                                source_end = f"{result['latest_file']}:{result['latest_line']}"
                                binary_start = f"0x{result['start_addr']}"
                                binary_end = f"0x{result['end_addr']}"
                                symbol = result.get('start_symbol', 'N/A')
                                start_off = result.get('start_offset', 'N/A')
                                end_off = result.get('end_offset', 'N/A')

                                output_str = f"{source_start}, {source_end}, {binary_start}, {binary_end}, {symbol}, {start_off}, {end_off}"
                                results["SUCCESS"].append((file_path, output_str))
                                result_line = f"  -> {output_str}"
                                print(result_line)
                                output_file.write(result_line + "\n")
                            else:
                                results["NOT_FOUND"].append(file_path)
                                result_line = "  -> Addresses not found"
                                print(result_line)
                                output_file.write(result_line + "\n")
                    print()
                    output_file.write("\n")
                    output_file.flush()  # Ensure data is written immediately
            except Exception as e:
                with print_lock:
                    completed_count += 1
                    header_line = f"[{completed_count}/{len(files)}] {file_path}"
                    print(header_line)
                    output_file.write(header_line + "\n")
                    result_line = f"  -> EXCEPTION: {e}"
                    print(result_line)
                    output_file.write(result_line + "\n")
                    results["ERROR"].append((file_path, str(e)))
                    print()
                    output_file.write("\n")
                    output_file.flush()  # Ensure data is written immediately

    # Close output file
    output_file.close()
    print(f"Results saved to {output_log_path}", file=sys.stderr)
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
    vmlinux_path = "./xkernel.vmlinux"
    modules_path = "../mods/modules/6.14.0-xkernel"

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

        # Also generate caches for modules
        print("\nGenerating caches for kernel modules...")
        module_files = find_module_files(modules_path)
        for module_name, ko_path in module_files.items():
            print(f"Generating cache for module {module_name}...")
            module_cache_dir = get_module_cache_dir(ko_path)
            generate_nm_cache(ko_path, module_cache_dir)
            generate_readelf_cache(ko_path, module_cache_dir)

        print("Cache generation complete!")
        sys.exit(0)

    # Load vmlinux caches
    nm_output = load_nm_cache(vmlinux_path, cache_dir)
    readelf_output = load_readelf_cache(vmlinux_path, cache_dir)

    if not nm_output:
        print("Error: Failed to load nm cache", file=sys.stderr)
        sys.exit(1)

    if not readelf_output:
        print("Error: Failed to load readelf cache", file=sys.stderr)
        sys.exit(1)

    # Load module information
    print("\nLoading kernel module information...")
    module_files = find_module_files(modules_path)
    module_nm_cache, module_readelf_cache = load_module_caches(module_files)

    # Build symbol-to-module mapping from nm output (more complete than Module.symvers)
    symbol_to_module = build_symbol_to_module_map(module_nm_cache, module_files)

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

        batch_process(directory, vmlinux_path, nm_output, readelf_output, max_workers,
                     symbol_to_module, module_nm_cache, module_readelf_cache)
    else:
        output_file = sys.argv[1]
        process_single_file(output_file, vmlinux_path, nm_output, readelf_output, verbose=True,
                          symbol_to_module=symbol_to_module,
                          module_nm_cache=module_nm_cache, module_readelf_cache=module_readelf_cache)


if __name__ == '__main__':
    main()

