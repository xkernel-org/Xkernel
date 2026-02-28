#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# python smart_diff.py tmp/diff/pre.disas.txt tmp/diff/post.disas.txt

import argparse
import re
from pathlib import Path

args = argparse.ArgumentParser()
args.add_argument("pre_o", type=str)
args.add_argument("post_o", type=str)
args = args.parse_args()

args.pre_o = Path(args.pre_o).resolve()
args.post_o = Path(args.post_o).resolve()

def read_sections(file_path):
    sections = {}
    pattern = re.compile(r".*? <(.*?)>:")
    section_irs = []
    last_section_name = None
    with open(file_path, "r") as f:
        for line in f:
            match = pattern.match(line)
            if match:
                # new section
                if last_section_name is not None:
                    sections[last_section_name] = section_irs
                last_section_name = match.group(1)
                section_irs = []
            else:
                section_irs.append(line)
        if last_section_name is not None:
            sections[last_section_name] = section_irs
    return sections

# instructions in a section looks like:
# 4220:       f3 0f 1e fa             endbr64 
# 4224:       e8 00 00 00 00          call   4229 <__blk_throtl_bio+0x9>
# 4229:       55                      push   %rbp
# 422a:       48 89 e5                mov    %rsp,%rbp
# 422d:       41 57                   push   %r15
# 422f:       41 56                   push   %r14
# 4231:       41 55                   push   %r13   # comment
# we don't need address and machine code, we only need instruction names
def is_hex(s):
    # Check if the string is a hexadecimal number
    return bool(re.fullmatch(r'[0-9a-fA-F]+', s))

def extract_instruction_line(line):
    # Parse a disassembly line and extract the instruction part
    line = line.strip()
    if line.startswith('# '):
        line = line[2:]

    # Split by colon to get the machine code and instruction part
    parts = line.split(':', 1)
    if len(parts) < 2:
        return ""

    code_part = parts[1].strip()
    tokens = code_part.split()
    i = 0
    while i < len(tokens) and len(tokens[i]) == 2 and is_hex(tokens[i]):
        i += 1
    if i < len(tokens):
        # Extract instruction and its arguments, remove comments
        ins = ' '.join(tokens[i:])
        if '#' in ins:
            ins = ins.split('#', 1)[0].rstrip()
        return ins
    return ""

def extract_instruction_names(section_irs):
    instruction_names = []
    for line in section_irs:
        ins = extract_instruction_line(line)
        if ins == "":
            continue
        instruction_names.append(ins)
    return instruction_names

def is_jump_or_call(ins):
    return ins.startswith("j") or ins.startswith("call")

def compare_instruction_names(pre_ins, post_ins):
    # Compare instruction names in pre_ins and post_ins
    # Note that for jump or call instructions, we only care about whether the relative address is changed
    # e.g., the relative address of <xxxxxx+0x123> is 0x123
    pattern = r'\+(0x[0-9a-fA-F]+)'
    diff_ins = []

    for (pre_ins, post_ins) in zip(pre_ins, post_ins):
        if pre_ins not in post_ins:
            if is_jump_or_call(pre_ins) and is_jump_or_call(post_ins):
                pre_match = re.search(pattern, pre_ins)
                post_match = re.search(pattern, post_ins)
                if pre_match and post_match:
                    pre_relative_address = int(pre_match.group(1), 16)
                    post_relative_address = int(post_match.group(1), 16)
                    if pre_relative_address == post_relative_address:
                        continue
                else:
                    continue
            diff_ins.append(pre_ins)
    
    return diff_ins

if __name__ == "__main__":
    pre_sections = read_sections(args.pre_o)
    post_sections = read_sections(args.post_o)

    if (len(pre_sections) != len(post_sections)):
        print("Error: Number of sections in pre and post are different")
        exit(1)

    diff_ins = []
    # compare all sections
    for section in pre_sections:
        pre_ins = extract_instruction_names(pre_sections[section])
        post_ins = extract_instruction_names(post_sections[section])
        diff_in = compare_instruction_names(pre_ins, post_ins)
        if diff_in:
            diff_ins.append({section: diff_in})

    for ins in diff_ins:
        for section in ins:
            print("[" + section + "]")
            for ins in ins[section]:
                print(ins)
            print()

