#!/usr/bin/env python3
"""X-tune stub generator for KernelX (§3.6 of paper).

Generates a fresh X-tune policy stub for a given ConstID from the scope table.
This is the `xkernel-tool gen` command, corresponding to the paper's `x-gen` tool.

The generated stub includes:
  - The SIE indirection header (#include of the auto-generated .bpf.h)
  - X_TUNE policy skeleton for user to fill in
  - Boilerplate: safety guard (x_transition_done), x_set call

Users edit the generated .bpf.c file to implement their tuning policy,
then load it via `xkernel-tool load <mode> <ConstID>`.
"""

import os
import re
import sys
from typing import Optional


SCOPE_TABLE_PATH = "/dev/shm/xkernel/scope_table"


def read_scope_entry(const_id: str) -> Optional[dict]:
    """Read a scope table entry for a given ConstID.

    Returns dict with keys: ConstID, Val, Expression, CS_Index, SS_Index,
                            BPF_File, Status, Candidates
    """
    if not os.path.exists(SCOPE_TABLE_PATH):
        return None

    with open(SCOPE_TABLE_PATH, 'r') as f:
        lines = f.readlines()

    if not lines:
        return None

    header = lines[0].rstrip('\n').split('\t')
    try:
        cid_col = header.index('ConstID')
    except ValueError:
        return None

    for line in lines[1:]:
        fields = line.rstrip('\n').split('\t')
        if len(fields) > cid_col and fields[cid_col] == const_id:
            return dict(zip(header, fields))

    return None


def parse_kprobe_info_from_stub(stub_h_path: str) -> list:
    """Extract kprobe info from the auto-generated .bpf.h header.

    Returns list of dicts: {index, function, offset, type, relationship}
    """
    if not os.path.exists(stub_h_path):
        return []

    with open(stub_h_path, 'r') as f:
        content = f.read()

    kprobes = []
    # Match X_TUNE_N macro definitions to extract function+offset
    for m in re.finditer(
        r'#define X_TUNE_(\d+)\(func_name, location_str\)', content
    ):
        idx = int(m.group(1))
        kprobes.append({'index': idx})

    # Match SIE helper comments for type info
    for m in re.finditer(
        r'// SIE helper (\d+): (\S+)', content
    ):
        idx = int(m.group(1))
        sie_type = m.group(2)
        for kp in kprobes:
            if kp['index'] == idx:
                kp['type'] = sie_type

    return kprobes


def generate_xtune_stub(const_id: str, output_path: Optional[str] = None) -> Optional[str]:
    """Generate an X-tune policy stub for a ConstID.

    Args:
        const_id: ConstID string (e.g., "1")
        output_path: Optional output file path. If None, writes to
                     bpf/stubs/xtune_stub_<ConstID>.bpf.c (overwriting).

    Returns:
        Path to generated file, or None on error.
    """
    entry = read_scope_entry(const_id)
    if not entry:
        print(f"Error: ConstID {const_id} not found in Scope Table")
        print(f"  Run 'xkernel-tool build' first to populate the scope table.")
        return None

    bpf_file = entry.get('BPF_File', '')
    val = entry.get('Val', '0')
    expression = entry.get('Expression', '')

    if not bpf_file:
        print(f"Error: No BPF file associated with ConstID {const_id}")
        return None

    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    stubs_dir = os.path.join(project_root, 'bpf', 'stubs')

    stub_name = bpf_file.replace('.bpf.o', '')  # e.g., "xtune_stub_1"
    stub_h = os.path.join(stubs_dir, f'{stub_name}.bpf.h')

    if not os.path.exists(stub_h):
        print(f"Error: Internal header not found: {stub_h}")
        print(f"  Run 'xkernel-tool build' first to generate SIE internals.")
        return None

    # Parse kprobe info from the generated header
    kprobes = parse_kprobe_info_from_stub(stub_h)

    if output_path is None:
        output_path = os.path.join(stubs_dir, f'{stub_name}.bpf.c')

    # Read existing .bpf.c to extract kprobe comments (function names, offsets)
    existing_c = os.path.join(stubs_dir, f'{stub_name}.bpf.c')
    kprobe_comments = []
    if os.path.exists(existing_c):
        with open(existing_c, 'r') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'// Kprobe (\d+): (.+?\+0x[0-9a-fA-F]+)\s*\((.+?)\)', line)
                if m:
                    kprobe_comments.append({
                        'num': int(m.group(1)),
                        'location': m.group(2),
                        'type': m.group(3),
                    })
                rm = re.match(r'// Relationship:\s+(.+)', line)
                if rm and kprobe_comments:
                    kprobe_comments[-1]['rel'] = rm.group(1)

    # Generate the stub
    lines = []
    lines.append('// SPDX-License-Identifier: GPL-2.0')
    lines.append(f'// X-tune policy for ConstID {const_id}')
    lines.append(f'// Expression: {expression}')
    lines.append(f'// Original value: {val}')
    lines.append('//')
    lines.append('// Edit the X_TUNE blocks below to implement your tuning policy.')
    lines.append('// Then load with: sudo ./xkernel-tool load <mode> ' + const_id)
    lines.append('')
    lines.append(f'#include "{stub_name}.bpf.h"')
    lines.append('')

    n_kprobes = max(len(kprobes), len(kprobe_comments))
    if n_kprobes == 0:
        n_kprobes = 1  # at least one stub

    for i in range(n_kprobes):
        # Write kprobe comment if available
        if i < len(kprobe_comments):
            kc = kprobe_comments[i]
            lines.append(f'// Kprobe {kc["num"]}: {kc["location"]} ({kc["type"]})')
            if 'rel' in kc:
                lines.append(f'// Relationship: {kc["rel"]}')

            # Parse function+offset for X_TUNE_N call
            m = re.match(r'(\S+)\+0x([0-9a-fA-F]+)', kc['location'])
            if m:
                func_name = m.group(1)
                offset_str = f'+0x{m.group(2)}'
            else:
                func_name = kc['location']
                offset_str = ''
        else:
            func_name = 'FUNCTION_NAME'
            offset_str = '+0xOFFSET'

        lines.append(f'X_TUNE_{i}({func_name}, "{offset_str}") {{')
        lines.append(f'    // Safety guard — MUST be first')
        lines.append(f'    if (!x_transition_done(x_ctx)) return 0;')
        lines.append(f'')
        lines.append(f'    // ─── Your tuning policy here ───')
        lines.append(f'    // Access kernel context via ctx (pt_regs):')
        lines.append(f'    //   struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);')
        lines.append(f'    //   u32 metric = BPF_CORE_READ(sk, sk_rcv_saddr);')
        lines.append(f'    //')
        lines.append(f'    // Set new value:')
        lines.append(f'    u64 val = {val}; // original value — change this')
        lines.append(f'    x_set(x_ctx, val);')
        lines.append(f'    return 0;')
        lines.append(f'}}')
        lines.append('')

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return output_path


def cmd_gen(args):
    """CLI handler for: xkernel-tool gen <ConstID> [-o output.bpf.c]"""
    if not args:
        print("Usage: xkernel-tool gen <ConstID> [-o output.bpf.c]")
        print()
        print("Generates an X-tune policy stub for a ConstID.")
        print("The stub includes safety guards and placeholder policy logic.")
        print("Edit the generated file, then load with: xkernel-tool load <mode> <ConstID>")
        sys.exit(1)

    const_id = args[0]
    output_path = None
    if '-o' in args:
        idx = args.index('-o')
        if idx + 1 < len(args):
            output_path = args[idx + 1]

    result = generate_xtune_stub(const_id, output_path)
    if result:
        print(f"Generated X-tune stub: {result}")
        print(f"  Edit the file to implement your policy, then:")
        print(f"  sudo ./xkernel-tool load <mode> {const_id}")
    else:
        sys.exit(1)
