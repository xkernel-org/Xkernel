#! /usr/bin/env python3

import pexpect
import argparse
import subprocess
import sys
import os
import logging
import re

OUTPUT = []

parser = argparse.ArgumentParser()
parser.add_argument("function_name", type=str, help="The target kernel function name. [E.g., hystart_update]")
parser.add_argument("-o", "--output_dir", type=str, help="The output directory. [E.g., ./gdb_output]", default="./gdb_output")
parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbose mode. Use -v for INFO level, -vv for DEBUG level")
args = parser.parse_args()

function_name = args.function_name
output_dir = args.output_dir
logger = logging.getLogger("simple")

kernel_full_name = None
kernel_no_postfix_name = None
kall_syms_base_address = 0

def log_init():
    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def xkernel_init():
    log_init()

def filter_ansi_colors(text):
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_kernel_source_path():
    """Dynamically detect the kernel source path"""
    try:
        # Get current kernel version
        kernel_version = subprocess.check_output("uname -r", shell=True).decode("utf-8").strip()
        kernel_no_postfix = kernel_version.split("-")[0]
        
        # Check for linux-source package
        source_path = f"/usr/src/linux-source-{kernel_no_postfix}"
        if os.path.exists(source_path):
            logger.info(f"Found kernel source at: {source_path}")
            return source_path
        
        # Check for linux-headers
        headers_path = f"/usr/src/linux-headers-{kernel_version}"
        if os.path.exists(headers_path):
            logger.info(f"Using kernel headers at: {headers_path}")
            return headers_path
        
        # Fallback to generic headers
        generic_headers_path = f"/usr/src/linux-headers-{kernel_no_postfix}-generic"
        if os.path.exists(generic_headers_path):
            logger.info(f"Using generic kernel headers at: {generic_headers_path}")
            return generic_headers_path
        
        logger.warning(f"Could not find kernel source/headers for version {kernel_version}")
        return None
        
    except Exception as e:
        logger.error(f"Error detecting kernel source path: {e}")
        return None

def get_address_from_kallsyms(function_name):
    try:
        cmd = f"sudo grep -A1 -E '^[0-9a-fA-F]+ [a-zA-Z] {function_name}$' /proc/kallsyms"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Error: can't find start address for {function_name} in /proc/kallsyms")
        
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            raise Exception(f"Error: can't extract end address for {function_name}")
            
        return lines[0].split(" ")[0], lines[1].split(" ")[0]
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def execute_gdb_cmd(gdb_session, cmd):
    logger.debug(f"Execute gdb command: {cmd}")
    gdb_session.sendline(cmd)
    index = gdb_session.expect([r"\(gdb\)", pexpect.TIMEOUT], timeout=30)
    if index == 1:  # TIMEOUT
        logger.warning(f"Command '{cmd}' timed out, trying to continue...")
        gdb_session.sendline("")  # Send empty line to get prompt back
        gdb_session.expect(r"\(gdb\)", timeout=10)

def execute_gdb_cmd_with_output(gdb_session, cmd):
    """Execute gdb command and capture output, especially for long outputs like disassemble"""
    logger.debug(f"Execute gdb command with output: {cmd}")
    gdb_session.sendline(cmd)
    
    try:
        index = gdb_session.expect([r"\(gdb\)", pexpect.TIMEOUT], timeout=60)
        output = gdb_session.before
        output = filter_ansi_colors(output)
        
        if index == 1:  # TIMEOUT
            logger.warning(f"Command '{cmd}' timed out")
            gdb_session.sendline("")  # Send empty line to get prompt back
            gdb_session.expect(r"\(gdb\)", timeout=10)
            return output
        else:
            return output
    except pexpect.EOF:
        logger.error("GDB session ended unexpectedly")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ""

def dump_assembly(start_address, end_address):
    cmd = f"sudo objdump -d --start-address=0x{start_address:x} --stop-address=0x{end_address:x} /proc/kcore"
    logger.info(f"Dump assembly:: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def run_gdb():
    global kernel_full_name, kernel_no_postfix_name, kall_syms_base_address

    kernel_full_name = subprocess.check_output("uname -r", shell=True).decode("utf-8").strip()
    kernel_no_postfix_name = kernel_full_name.split("-")[0]

    vm_linux_file = f"/usr/lib/debug/boot/vmlinux-{kernel_full_name}"

    if not os.path.exists(vm_linux_file):
        logger.error(f"File {vm_linux_file} does not exist")
        sys.exit(1)
    
    # Get start address of function
    # addr2line -e /usr/lib/debug/boot/vmlinux-6.8.0-59-generic -a -i
    addr2line_cmd = f"addr2line -e {vm_linux_file} -a -i {function_name}"
    result = subprocess.run(addr2line_cmd, shell=True, capture_output=True, text=True, timeout=30)
    output = result.stdout
    
    vm_linux_base_address = int(output.split("\n")[0], 16)
    kall_syms_base_address = int(get_address_from_kallsyms(function_name)[0], 16)
    
    OFFSET = kall_syms_base_address - vm_linux_base_address

    print(f"KASLR OFFSET: 0x{OFFSET:x}")

    # Get kernel source path dynamically
    kernel_source_path = get_kernel_source_path()
    
    # Build gdb command with dynamic source path
    gdb_cmd = f"gdb -q {vm_linux_file} -ex 'set confirm off' -ex 'set height 0'"
    
    # Add substitute-path only if we found a valid source path
    if kernel_source_path:
        # Try to find the build path from debug info
        try:
            # Use gdb to get the build path from debug info
            temp_gdb_cmd = f"gdb -q {vm_linux_file} -ex 'info sources' -ex 'quit'"
            result = subprocess.run(temp_gdb_cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            # Look for build path patterns
            build_path_pattern = r'/build/[^/]+/linux-[^/]+'
            build_path_match = re.search(build_path_pattern, output)
            
            if build_path_match:
                build_path = build_path_match.group(0)
                gdb_cmd += f" -ex 'set substitute-path {build_path} {kernel_source_path}'"
                logger.info(f"Setting substitute-path: {build_path} -> {kernel_source_path}")
            else:
                logger.warning("Could not detect build path from debug info, skipping substitute-path")
        except Exception as e:
            logger.warning(f"Error detecting build path: {e}, skipping substitute-path")
    
    gdb_cmd += f" -ex 'list {function_name}' -ex 'disassemble /m {function_name}' -ex 'quit'"
    logger.debug(f"Execute gdb command: {gdb_cmd}")
    
    try:
        # Use subprocess to capture the complete output
        result = subprocess.run(gdb_cmd, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout
        
        # Filter ANSI color codes
        output = filter_ansi_colors(output)
        
        # Add OFFSET to all addresses in the output
        def add_offset_to_addresses(text, offset):
            """Add OFFSET to all hex addresses in the text"""
            import re
            # Pattern to match instruction addresses like 0xffffffff81169070 <+592>:
            # This pattern specifically matches addresses that appear at the start of instruction lines
            address_pattern = r'^(\s*)(0x[0-9a-fA-F]+)\s*<\+[0-9]+>:\s*(.*)$'
            
            def replace_address(match):
                indent = match.group(1)
                addr_str = match.group(2)
                rest_of_line = match.group(3)
                try:
                    addr_int = int(addr_str, 16)
                    new_addr = addr_int + offset
                    return f"{indent}0x{new_addr:x} <+{match.group(0).split('<+')[1].split('>')[0]}>:{rest_of_line}"
                except ValueError:
                    return match.group(0)
            
            return re.sub(address_pattern, replace_address, text, flags=re.MULTILINE)
        
        # Apply OFFSET to all addresses
        output = add_offset_to_addresses(output, OFFSET)
        
        # Save output
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = f"{output_dir}/gdb_{function_name}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Disassembly of function: {function_name}\n")
            f.write(f"# Generated by gdb.py\n")
            f.write(f"# Kernel version: {kernel_full_name}\n")
            if kernel_source_path:
                f.write(f"# Source path: {kernel_source_path}\n")
            f.write(f"# KASLR OFFSET applied: 0x{OFFSET:x}\n")
            f.write("\n")
            f.write(output)
        
        logger.info(f"Disassembly output saved to gdb.txt")
        
    except subprocess.TimeoutExpired:
        logger.error("GDB command timed out")
    except Exception as e:
        logger.error(f"Error running GDB: {str(e)}")

if __name__ == "__main__":
    xkernel_init()
    run_gdb()