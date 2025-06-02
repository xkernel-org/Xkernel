import pexpect
import argparse
import subprocess
import sys
import logging

OUTPUT = []

parser = argparse.ArgumentParser()
parser.add_argument("function_name", type=str, help="The target kernel function name. [E.g., hystart_update]")
parser.add_argument("line_number_list", type=str, help="The target kernel line number. [E.g., 434, 435]")
parser.add_argument("-e", "--expression_if", action="store_true", help="Whether this line is a if expression. [E.g., True]")
parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbose mode. Use -v for INFO level, -vv for DEBUG level")
args = parser.parse_args()

function_name = args.function_name
line_number_list = args.line_number_list
expression_if = args.expression_if
logger = logging.getLogger("simple")
kernel_full_name = None
kernel_no_postfix_name = None

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

def get_address_from_kallsyms(function_name):
    try:
        # Use grep to find the function and its next line
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
    gdb_session.expect_exact("(gdb)")

def dump_assembly(start_address, end_address):
    cmd = f"sudo objdump -d --start-address=0x{start_address:x} --stop-address=0x{end_address:x} /proc/kcore"
    logger.info(f"Dump assembly:: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def run_gdb():

    kernel_full_name = subprocess.check_output("uname -r", shell=True).decode("utf-8").strip()
    kernel_no_postfix_name = kernel_full_name.split("-")[0]
    gdb_cmd = f"gdb /usr/lib/debug/boot/vmlinux-{kernel_full_name}"

    # Start gdb session
    gdb_session = pexpect.spawn(gdb_cmd, encoding='utf-8', timeout=10)
    gdb_session.expect_exact("(gdb)")

    # Set substitute path
    execute_gdb_cmd(gdb_session, f"set substitute-path /build/linux-Rb6idR/linux-{kernel_no_postfix_name} /usr/src/linux-source-{kernel_no_postfix_name}")

    execute_gdb_cmd(gdb_session, f"list {function_name}")

    execute_gdb_cmd(gdb_session, f'info line {function_name}')
    output = gdb_session.before.splitlines()
    output = output[3]
    
    vm_linux_start_address = output.split("starts at address ")[1].split(" <")[0]
    vm_linux_start_address = vm_linux_start_address.replace("\x1b[34m", "").replace("\x1b[m", "")
    vm_linux_start_address = int(vm_linux_start_address, 16)

    kall_syms_start_address, _ = get_address_from_kallsyms(function_name)
    kall_syms_start_address = int(kall_syms_start_address, 16)

    OFFSET = kall_syms_start_address - vm_linux_start_address
    
    kall_syms_base_address = kall_syms_start_address

    logger.info(f"Start address in vmlinux: \t0x{vm_linux_start_address:x}")
    logger.info(f"Start address in kallsyms: \t0x{kall_syms_start_address:x}")
    logger.info(f"Offset because of KASLR: \t0x{OFFSET:x}")

    merge_start_address = None
    merge_end_address = None
    for line_number in line_number_list.split(","):
        execute_gdb_cmd(gdb_session, f"info line {line_number}")
        output = gdb_session.before.splitlines()
        info_output = "\n".join(line for line in output if f"info line {line_number}" not in line)
        logger.debug(f"Info output: {info_output}")

        if (len(info_output.split("starts at address ")) == 1):
            address = info_output.split("is at address")[1].split("<")[0].split("m")[1].split('\x1b')[0]
            execute_gdb_cmd(gdb_session, f"info line *{address}")
            output = gdb_session.before.splitlines()
            info_output = "\n".join(line for line in output if f"info line *{address}" not in line)
            logger.debug(f"Info output: {info_output}")

        vm_linux_start_address = info_output.split("starts at address ")[1].split(" <")[0]
        vm_linux_start_address = vm_linux_start_address.replace("\x1b[34m", "").replace("\x1b[m", "")

        vm_linux_end_address = info_output.split("ends at ")[1].split(" <")[0]
        vm_linux_end_address = vm_linux_end_address.replace("\x1b[34m", "").replace("\x1b[m", "")

        if merge_start_address is None:
            merge_start_address = vm_linux_start_address
            merge_start_address = int(merge_start_address, 16)
        
        merge_end_address = vm_linux_end_address

    merge_end_address = int(merge_end_address, 16)
    execute_gdb_cmd(gdb_session, f"x/i 0x{merge_end_address:x}")

    output = gdb_session.before.splitlines()
    output = output[2].split(' ')[4].split('\x1b[32m')[1]
    
    if (expression_if):
        if (output[0] != 'j'):

            logger.info("This line is a if expression, but we found that the end address is not a jmp instruction.")
            logger.info("Continue searching until a jmp instruction is found.")

            execute_gdb_cmd(gdb_session, f'info line *0x{merge_end_address:x}')
            output = gdb_session.before.splitlines()
            info_output = "\n".join(line for line in output if f"info line {line_number}" not in line)

            merge_end_address = info_output.split("ends at ")[1].split(" <")[0]
            merge_end_address = merge_end_address.replace("\x1b[34m", "").replace("\x1b[m", "")
            merge_end_address = int(merge_end_address, 16)

    kall_syms_start_address = merge_start_address + OFFSET
    kall_syms_end_address = merge_end_address + OFFSET

    OUTPUT.append(f"Base address of {function_name}: 0x{kall_syms_base_address:x}")
    OUTPUT.append(f"[{function_name}@{line_number_list}]")
    OUTPUT.append(f"Start address in kallsyms: \t0x{kall_syms_start_address:x}")
    OUTPUT.append(f"End address in kallsyms: \t0x{kall_syms_end_address:x}\n")

    # Close gdb session
    gdb_session.close()

    return kall_syms_start_address, kall_syms_end_address

def run_objdump(kall_syms_start_address, kall_syms_end_address):
    assembly = dump_assembly(kall_syms_start_address, kall_syms_end_address)
    OUTPUT.append(assembly)

if __name__ == "__main__":

    xkernel_init()

    kall_syms_start_address, kall_syms_end_address = run_gdb()

    run_objdump(kall_syms_start_address, kall_syms_end_address)

    print("\n------------------------------------OUTPUT------------------------------------")
    print("\n".join(OUTPUT))
    print("--------------------------------------------------------------------------------")