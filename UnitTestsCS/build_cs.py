#!/usr/bin/env python3
"""
Symbolic execution engine for x86 Basic Blocks.
Reads res_*.txt files, parses Basic Blocks, and performs symbolic execution.
"""

import re
import os
import glob
from collections import OrderedDict
from typing import Dict, List, Tuple, Optional, Set


class SymbolicExecutor:
    """Symbolic execution engine for x86 instructions."""
    
    def __init__(self):
        # Register mapping: real register -> anonymous register (r0, r1, r2, ...)
        self.reg_map: Dict[str, str] = {}
        self.reg_counter = 0
        
        # Symbolic state: anonymous register -> expression
        self.state: Dict[str, str] = {}
        
        # Memory state (simplified: address -> expression)
        self.memory: Dict[str, str] = {}
        
        # Track which registers have been used
        self.used_regs: Set[str] = set()
        
    def get_base_register(self, reg_name: str) -> str:
        """Get the base register name from a sub-register.
        e.g., 'r13b' -> 'r13', 'eax' -> 'rax' (on x86-64), 'al' -> 'rax'
        """
        reg_name = reg_name.lower()
        
        # Map 32-bit to 64-bit base registers
        reg32_to_64 = {
            'eax': 'rax', 'ebx': 'rbx', 'ecx': 'rcx', 'edx': 'rdx',
            'esi': 'rsi', 'edi': 'rdi', 'ebp': 'rbp', 'esp': 'rsp',
            'r8d': 'r8', 'r9d': 'r9', 'r10d': 'r10', 'r11d': 'r11',
            'r12d': 'r12', 'r13d': 'r13', 'r14d': 'r14', 'r15d': 'r15'
        }
        
        # Map 16-bit to 64-bit base registers
        reg16_to_64 = {
            'ax': 'rax', 'bx': 'rbx', 'cx': 'rcx', 'dx': 'rdx',
            'si': 'rsi', 'di': 'rdi', 'bp': 'rbp', 'sp': 'rsp'
        }
        
        # Map 8-bit to 64-bit base registers
        reg8_to_64 = {
            'al': 'rax', 'bl': 'rbx', 'cl': 'rcx', 'dl': 'rdx',
            'sil': 'rsi', 'dil': 'rdi', 'bpl': 'rbp', 'spl': 'rsp',
            'r8b': 'r8', 'r9b': 'r9', 'r10b': 'r10', 'r11b': 'r11',
            'r12b': 'r12', 'r13b': 'r13', 'r14b': 'r14', 'r15b': 'r15'
        }
        
        if reg_name in reg32_to_64:
            return reg32_to_64[reg_name]
        elif reg_name in reg16_to_64:
            return reg16_to_64[reg_name]
        elif reg_name in reg8_to_64:
            return reg8_to_64[reg_name]
        else:
            # Already a 64-bit register or unknown
            return reg_name
    
    def get_anonymous_reg(self, real_reg: str) -> str:
        """Get or create anonymous register for a real register.
        Sub-registers (like %r13b, %r13d) map to the same base register.
        """
        # Normalize register name
        real_reg = real_reg.lower().strip()
        
        # Get base register name
        base_reg = self.get_base_register(real_reg)
        
        if base_reg not in self.reg_map:
            anon_reg = f"r{self.reg_counter}"
            self.reg_counter += 1
            self.reg_map[base_reg] = anon_reg
            self.used_regs.add(anon_reg)
            return anon_reg
        return self.reg_map[base_reg]
    
    def parse_instruction(self, line: str) -> Optional[Tuple[str, str, List[str]]]:
        """Parse an instruction line.
        Returns: (address, mnemonic, operands) or None
        """
        # Remove [*] marker if present
        line = re.sub(r'^\s*\[\*\]\s*', '', line)
        
        # Match: "  address:  bytes    mnemonic operands"
        match = re.match(r'^\s*([0-9a-fA-F]+):\s+[0-9a-f\s]+\s+(\S+)\s+(.*)$', line)
        if not match:
            return None
        
        address = match.group(1)
        mnemonic = match.group(2)
        operands_str = match.group(3).strip()
        
        # Parse operands (comma-separated)
        operands = [op.strip() for op in operands_str.split(',')] if operands_str else []
        
        return (address, mnemonic, operands)
    
    def parse_operand(self, operand: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parse an operand into (type, value, register).
        Returns: (type, immediate_value_or_memory_expr, register_name)
        Types: 'imm', 'reg', 'mem'
        """
        operand = operand.strip()
        
        # Immediate value: $0x123 or $123
        if operand.startswith('$'):
            imm_str = operand[1:]
            # Try to parse as hex or decimal
            try:
                if imm_str.startswith('0x') or imm_str.startswith('0X'):
                    value = int(imm_str, 16)
                else:
                    value = int(imm_str, 10)
                return ('imm', f"0x{value:x}", None)
            except ValueError:
                return ('imm', imm_str, None)
        
        # Memory access: offset(%reg) or (%reg) or offset(%reg,%reg,scale)
        mem_match = re.match(r'(-?0x[0-9a-fA-F]+|-?\d+)?\(([^)]+)\)', operand)
        if mem_match:
            offset = mem_match.group(1) or "0"
            regs_str = mem_match.group(2)
            
            # Parse register(s) and scale
            # Format: %reg or %reg,%reg or %reg,%reg,scale
            reg_parts = [p.strip() for p in regs_str.split(',')]
            base_reg = reg_parts[0] if reg_parts else None
            index_reg = reg_parts[1] if len(reg_parts) > 1 else None
            scale = reg_parts[2] if len(reg_parts) > 2 else "1"
            
            if base_reg:
                base_reg = base_reg.lstrip('%')
                base_anon = self.get_anonymous_reg(base_reg)
            else:
                base_anon = None
            
            if index_reg:
                index_reg = index_reg.lstrip('%')
                index_anon = self.get_anonymous_reg(index_reg)
            else:
                index_anon = None
            
            # Build memory expression
            mem_expr_parts = []
            if offset != "0":
                mem_expr_parts.append(offset)
            if base_anon:
                mem_expr_parts.append(base_anon)
            if index_anon:
                if scale != "1":
                    mem_expr_parts.append(f"{index_anon}*{scale}")
                else:
                    mem_expr_parts.append(index_anon)
            
            mem_expr = "+".join(mem_expr_parts) if mem_expr_parts else "0"
            return ('mem', f"[{mem_expr}]", base_reg)
        
        # Register: %rax, %eax, %al, etc.
        if operand.startswith('%'):
            reg_name = operand[1:]
            anon_reg = self.get_anonymous_reg(reg_name)
            return ('reg', None, reg_name)
        
        # Label or other (for jumps/calls)
        return ('label', operand, None)
    
    def execute_instruction(self, mnemonic: str, operands: List[str]) -> str:
        """Execute an instruction symbolically.
        Returns: description of the operation performed.
        """
        if not operands:
            return f"{mnemonic} (no operands)"
        
        # Handle different instruction types
        mnemonic_lower = mnemonic.lower()
        
        # MOV: mov src, dst
        if mnemonic_lower == 'mov':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    
                    if src_type == 'imm':
                        # mov $imm, %reg
                        self.state[dst_anon] = src_val
                        return f"{dst_anon} = {src_val}"
                    elif src_type == 'reg' and src_reg:
                        # mov %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        self.state[dst_anon] = src_expr
                        return f"{dst_anon} = {src_expr}"
                    elif src_type == 'mem':
                        # mov [mem], %reg
                        mem_expr = f"mem{src_val}"
                        self.state[dst_anon] = mem_expr
                        return f"{dst_anon} = {mem_expr}"
                elif dst_type == 'mem' and src_type == 'reg' and src_reg:
                    # mov %reg, [mem]
                    src_anon = self.get_anonymous_reg(src_reg)
                    src_expr = self.state.get(src_anon, src_anon)
                    mem_expr = dst_val
                    self.memory[mem_expr] = src_expr
                    return f"{mem_expr} = {src_expr}"
        
        # ADD: add src, dst
        elif mnemonic_lower == 'add':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        # add $imm, %reg
                        new_expr = f"({dst_expr} + {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # add %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} + {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # SUB: sub src, dst
        elif mnemonic_lower == 'sub':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        # sub $imm, %reg
                        new_expr = f"({dst_expr} - {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # sub %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} - {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # AND: and src, dst
        elif mnemonic_lower == 'and':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        # and $imm, %reg
                        new_expr = f"({dst_expr} & {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # and %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} & {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # OR: or src, dst
        elif mnemonic_lower == 'or':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        new_expr = f"({dst_expr} | {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} | {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # XOR: xor src, dst
        elif mnemonic_lower == 'xor':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        new_expr = f"({dst_expr} ^ {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} ^ {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # SHL: shl %cl, %reg or shl $imm, %reg
        elif mnemonic_lower == 'shl':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'reg' and src_reg:
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} << {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # MOVZBL: movzbl src, dst (zero-extend byte to long)
        elif mnemonic_lower == 'movzbl':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    
                    if src_type == 'reg' and src_reg:
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"zext({src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'mem':
                        mem_expr = f"mem{src_val}"
                        new_expr = f"zext({mem_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # SBB: sbb src, dst (subtract with borrow)
        elif mnemonic_lower == 'sbb':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'reg' and src_reg:
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        # SBB: dst = dst - src - CF
                        new_expr = f"({dst_expr} - {src_expr} - CF)"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # CMP: cmp src, dst (compare, sets flags)
        elif mnemonic_lower == 'cmp' or mnemonic_lower == 'test':
            # Comparison doesn't modify registers, just sets flags
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                src_expr = None
                if src_type == 'imm':
                    src_expr = src_val
                elif src_type == 'reg' and src_reg:
                    src_anon = self.get_anonymous_reg(src_reg)
                    src_expr = self.state.get(src_anon, src_anon)
                
                dst_expr = None
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                
                if src_expr and dst_expr:
                    return f"FLAGS = cmp({dst_expr}, {src_expr})"
        
        # Jumps and calls (no register modification)
        elif mnemonic_lower in ['jae', 'jb', 'je', 'jne', 'ja', 'jbe', 'jl', 'jle', 'jg', 'jge', 'jmp', 'call']:
            if operands:
                target = operands[0]
                return f"{mnemonic.upper()} {target} (control flow)"
        
        # Default: unknown instruction
        return f"{mnemonic} {', '.join(operands)} (not fully supported)"
    
    def get_all_expressions(self) -> Dict[str, str]:
        """Get all current symbolic expressions."""
        return dict(self.state)
    
    def reset(self):
        """Reset the symbolic executor state."""
        self.reg_map.clear()
        self.state.clear()
        self.memory.clear()
        self.reg_counter = 0
        self.used_regs.clear()


def parse_basic_block(lines: List[str]) -> Tuple[Optional[str], Optional[str], List[str]]:
    """Parse a Basic Block from lines.
    Returns: (function_name, lines_info, instruction_lines)
    """
    if not lines:
        return (None, None, [])
    
    function_name = None
    lines_info = None
    instructions = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match "Basic Block: lines xxx-xxx"
        bb_match = re.match(r'^Basic Block:\s+lines\s+(\d+)-(\d+)$', line)
        if bb_match:
            lines_info = line
            continue
        
        # Match "Function: function_name"
        func_match = re.match(r'^Function:\s+(.+)$', line)
        if func_match:
            function_name = func_match.group(1)
            continue
        
        # Match instruction line: "  address:  bytes    mnemonic operands"
        if re.match(r'^\s*(\[*\*\]\s*)?[0-9a-fA-F]+:', line):
            instructions.append(line)
    
    return (function_name, lines_info, instructions)


def process_res_file(filepath: str):
    """Process a single res_*.txt file."""
    print(f"\n{'='*80}")
    print(f"Processing: {filepath}")
    print(f"{'='*80}\n")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split into Basic Blocks (separated by "Basic Block:" lines)
    blocks = []
    current_block_lines = []
    
    for line in content.split('\n'):
        if line.strip().startswith('Basic Block:'):
            if current_block_lines:
                blocks.append(current_block_lines)
            current_block_lines = [line]
        elif current_block_lines:
            current_block_lines.append(line)
    
    if current_block_lines:
        blocks.append(current_block_lines)
    
    # Process each Basic Block
    for block_idx, block_lines in enumerate(blocks):
        function_name, lines_info, instructions = parse_basic_block(block_lines)
        
        if not instructions:
            continue
        
        print(f"\n--- Basic Block {block_idx + 1} ---")
        if lines_info:
            print(lines_info)
        if function_name:
            print(f"Function: {function_name}")
        print()
        
        # Create a new symbolic executor for this Basic Block
        executor = SymbolicExecutor()
        
        # Execute each instruction
        for inst_line in instructions:
            # Remove [*] marker for parsing
            clean_line = re.sub(r'^\s*\[\*\]\s*', '', inst_line)
            
            parsed = executor.parse_instruction(clean_line)
            if not parsed:
                print(f"  {inst_line}")
                print(f"    (Could not parse instruction)")
                continue
            
            address, mnemonic, operands = parsed
            
            # Print instruction
            print(f"  {inst_line}")
            
            # Execute symbolically
            result = executor.execute_instruction(mnemonic, operands)
            print(f"    -> {result}")
            
            # Print all current expressions
            expressions = executor.get_all_expressions()
            if expressions:
                print(f"    Expressions after this instruction:")
                for reg, expr in sorted(expressions.items()):
                    print(f"      {reg} = {expr}")
            print()


def main():
    """Main function."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    res_files = sorted(glob.glob(os.path.join(script_dir, 'res_*.txt')))
    
    if not res_files:
        print(f"No res_*.txt files found in {script_dir}")
        return
    
    print(f"Found {len(res_files)} result file(s)")
    
    for res_file in res_files:
        process_res_file(res_file)


if __name__ == '__main__':
    main()

