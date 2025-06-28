#! /usr/bin/env python3

import argparse
import subprocess

parser = argparse.ArgumentParser(description='Extract constants from Linux kernel source code')
parser.add_argument('--func', type=str, default='blk_mq_delay_run_hw_queue', help='Function name to search')
args = parser.parse_args()

def search_kallsyms(func_name: str) -> tuple[int, int]:
    cmd = f"sudo cat /proc/kallsyms |grep {func_name} -w -A1"
    output = subprocess.check_output(cmd, shell=True).decode("utf-8")
    start_address = output.split("\n")[0].split(" ")[0]
    stop_address = output.split("\n")[1].split(" ")[0]
    return start_address, stop_address

def calc_offset(start_address: int, input: str) -> str:
    lines = input.split("\n")
    output = ""
    for line in lines:
        line = line.strip(":")
        addr = line.split(" ")[0].split(":")[0]
        if (addr != '' and addr != '/proc/kcore' and addr != 'Disassembly'):
            offset = int(addr, 16) - start_address
            output += f"(+0x{offset:x}){line}\n"

    return output

def objdump(start_address: str, stop_address: str):
    start_address = int(start_address, 16)
    stop_address = int(stop_address, 16)
    cmd = f"sudo objdump -d --start-address={start_address} --stop-address={stop_address} /proc/kcore"

    output = subprocess.check_output(cmd, shell=True).decode("utf-8")
    
    output = calc_offset(start_address, output)
    print(output)

if __name__ == "__main__":
    start_address, stop_address = search_kallsyms(args.func)
    print(f"Start address: 0x{start_address}")
    print(f"Stop address:  0x{stop_address}")

    objdump(start_address, stop_address)

