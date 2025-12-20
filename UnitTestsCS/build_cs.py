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
                    
                    if src_type == 'imm':
                        # shl $imm, %reg
                        new_expr = f"({dst_expr} << {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # shl %reg, %reg
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} << {src_expr})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
        
        # SHR: shr %cl, %reg or shr $imm, %reg
        elif mnemonic_lower == 'shr':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    
                    if src_type == 'imm':
                        # shr $imm, %reg
                        new_expr = f"({dst_expr} >> {src_val})"
                        self.state[dst_anon] = new_expr
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # shr %reg, %reg
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} >> {src_expr})"
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


def process_res_file(filepath: str, return_expressions: bool = False):
    """Process a single res_*.txt file.
    
    Args:
        filepath: Path to the file to process
        return_expressions: If True, return list of (instruction, expressions) tuples
    
    Returns:
        If return_expressions is True: list of (instruction_line, address, expressions_dict) tuples
        Otherwise: None
    """
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
    
    expression_sequence = []  # List of (instruction_line, address, expressions_dict)
    
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
            
            # Get all current expressions
            expressions = executor.get_all_expressions()
            expressions_dict = dict(sorted(expressions.items()))
            
            if return_expressions:
                expression_sequence.append((inst_line, address, expressions_dict))
            
            if expressions:
                print(f"    Expressions after this instruction:")
                for reg, expr in sorted(expressions.items()):
                    print(f"      {reg} = {expr}")
            print()
    
    if return_expressions:
        return expression_sequence
    return None


def compare_expressions(seq1: List[Tuple[str, str, Dict[str, str]]], 
                       seq2: List[Tuple[str, str, Dict[str, str]]],
                       name1: str = "v1", name2: str = "v2") -> List[Tuple[int, str, str, Dict[str, str], Dict[str, str]]]:
    """Compare two expression sequences and find differences.
    
    Args:
        seq1: First sequence of (instruction, address, expressions)
        seq2: Second sequence of (instruction, address, expressions)
        name1: Name for first sequence
        name2: Name for second sequence
    
    Returns:
        List of (index, instruction1, instruction2, expr1, expr2) for differences
    """
    differences = []
    max_len = max(len(seq1), len(seq2))
    
    for i in range(max_len):
        if i >= len(seq1):
            # seq1 ended, seq2 continues
            inst2, addr2, expr2 = seq2[i]
            differences.append((i, None, inst2, {}, expr2))
        elif i >= len(seq2):
            # seq2 ended, seq1 continues
            inst1, addr1, expr1 = seq1[i]
            differences.append((i, inst1, None, expr1, {}))
        else:
            inst1, addr1, expr1 = seq1[i]
            inst2, addr2, expr2 = seq2[i]
            
            # Compare expressions
            if expr1 != expr2:
                differences.append((i, inst1, inst2, expr1, expr2))
    
    return differences


def find_changed_ranges(differences: List[Tuple[int, str, str, Dict[str, str], Dict[str, str]]]) -> List[Tuple[int, int]]:
    """Find contiguous ranges of changed instructions.
    
    Args:
        differences: List of (index, inst1, inst2, expr1, expr2) tuples
    
    Returns:
        List of (start_index, end_index) tuples representing changed ranges
    """
    if not differences:
        return []
    
    ranges = []
    start_idx = differences[0][0]
    end_idx = differences[0][0]
    
    for i in range(1, len(differences)):
        current_idx = differences[i][0]
        if current_idx == end_idx + 1:
            # Contiguous
            end_idx = current_idx
        else:
            # Gap found, save current range
            ranges.append((start_idx, end_idx))
            start_idx = current_idx
            end_idx = current_idx
    
    # Add last range
    ranges.append((start_idx, end_idx))
    
    return ranges


def print_expression_diff(prefix: str, seq1: List[Tuple[str, str, Dict[str, str]]],
                         seq2: List[Tuple[str, str, Dict[str, str]]],
                         seq3: List[Tuple[str, str, Dict[str, str]]] = None):
    """Print differences between expression sequences.
    
    Args:
        prefix: Prefix for output (e.g., "Test Group 1")
        seq1: v1 sequence
        seq2: v2 sequence
        seq3: v3 sequence (optional)
    """
    print(f"\n{'='*80}")
    print(f"{prefix} - Expression Differences")
    print(f"{'='*80}\n")
    
    # Compare v1 vs v2
    diff_v1_v2 = compare_expressions(seq1, seq2, "v1", "v2")
    if diff_v1_v2:
        ranges_v1_v2 = find_changed_ranges(diff_v1_v2)
        print(f"--- Differences between v1 (original) and v2 (recompiled from first command) ---")
        print(f"Changed instruction ranges: {ranges_v1_v2}")
        print()
        
        # Collect changed instructions from v1
        changed_v1 = []
        # Collect changed instructions from v2
        changed_v2 = []
        
        for idx, inst1, inst2, expr1, expr2 in diff_v1_v2:
            if inst1:
                changed_v1.append((idx + 1, inst1.strip()))
            if inst2:
                changed_v2.append((idx + 1, inst2.strip()))
        
        print("Changed instructions in v1:")
        for idx, inst in changed_v1:
            print(f"  Instruction {idx}: {inst}")
        print()
        
        print("Changed instructions in v2:")
        for idx, inst in changed_v2:
            print(f"  Instruction {idx}: {inst}")
        print()
    else:
        print("No differences between v1 and v2\n")
    
    # Compare v2 vs v3 if v3 exists
    if seq3:
        diff_v2_v3 = compare_expressions(seq2, seq3, "v2", "v3")
        if diff_v2_v3:
            ranges_v2_v3 = find_changed_ranges(diff_v2_v3)
            print(f"--- Differences between v2 (recompiled from first command) and v3 (recompiled from second command) ---")
            print(f"Changed instruction ranges: {ranges_v2_v3}")
            print()
            
            # Collect changed instructions from v2
            changed_v2 = []
            # Collect changed instructions from v3
            changed_v3 = []
            
            for idx, inst2, inst3, expr2, expr3 in diff_v2_v3:
                if inst2:
                    changed_v2.append((idx + 1, inst2.strip()))
                if inst3:
                    changed_v3.append((idx + 1, inst3.strip()))
            
            print("Changed instructions in v2:")
            for idx, inst in changed_v2:
                print(f"  Instruction {idx}: {inst}")
            print()
            
            print("Changed instructions in v3:")
            for idx, inst in changed_v3:
                print(f"  Instruction {idx}: {inst}")
            print()
        else:
            print("No differences between v2 and v3\n")
        
        # Compare v1 vs v3
        diff_v1_v3 = compare_expressions(seq1, seq3, "v1", "v3")
        if diff_v1_v3:
            ranges_v1_v3 = find_changed_ranges(diff_v1_v3)
            print(f"--- Differences between v1 (original) and v3 (recompiled from second command) ---")
            print(f"Changed instruction ranges: {ranges_v1_v3}")
            print()
            
            # Collect changed instructions from v1
            changed_v1 = []
            # Collect changed instructions from v3
            changed_v3 = []
            
            for idx, inst1, inst3, expr1, expr3 in diff_v1_v3:
                if inst1:
                    changed_v1.append((idx + 1, inst1.strip()))
                if inst3:
                    changed_v3.append((idx + 1, inst3.strip()))
            
            print("Changed instructions in v1:")
            for idx, inst in changed_v1:
                print(f"  Instruction {idx}: {inst}")
            print()
            
            print("Changed instructions in v3:")
            for idx, inst in changed_v3:
                print(f"  Instruction {idx}: {inst}")
            print()
        else:
            print("No differences between v1 and v3\n")


def extract_source_values(cmd_file: str) -> Dict[str, Tuple[int, int, int]]:
    """Extract source-level values V1, V2, V3 from cmd_v2.sh.
    
    Args:
        cmd_file: Path to cmd_v2.sh
        Format: First line contains "V1,V2,V3", followed by command pairs
    
    Returns:
        Dictionary mapping test group prefix to (V1, V2, V3) tuple
    """
    source_values = {}
    
    if not os.path.exists(cmd_file):
        return source_values
    
    with open(cmd_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return source_values
    
    # First line should contain V1,V2,V3
    first_line = lines[0].strip()
    if not first_line or first_line.startswith('#'):
        return source_values
    
    # Parse V1,V2,V3 from first line
    v_parts = [part.strip() for part in first_line.split(',')]
    if len(v_parts) != 3:
        return source_values
    
    try:
        v1 = int(v_parts[0])
        v2 = int(v_parts[1])
        v3 = int(v_parts[2])
    except ValueError:
        return source_values
    
    # Count command pairs to determine test groups
    # Each test group has 2 commands
    test_group = 1
    cmd_count = 0
    
    for line in lines[1:]:  # Skip first line
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Check if it's a command line
        if 'check_assembly_diff.py' in line:
            cmd_count += 1
            if cmd_count == 2:
                # Two commands form a test group
                source_values[str(test_group)] = (v1, v2, v3)
                test_group += 1
                cmd_count = 0
    
    # If there's only one command pair, use the values
    if test_group == 1 and cmd_count == 2:
        source_values['1'] = (v1, v2, v3)
    
    return source_values


def extract_immediate_values(inst_line: str) -> List[int]:
    """Extract immediate values from an instruction line.
    
    Args:
        inst_line: Instruction line from Basic Block file
    
    Returns:
        List of immediate values found in the instruction (as unsigned integers)
    """
    immediates = []
    
    # Remove [*] marker
    clean_line = re.sub(r'^\s*\[\*\]\s*', '', inst_line)
    
    # Find all immediate values (hex or decimal)
    # Pattern: $0x123 or $123
    # Also handle negative values like $0xff80 (which might be -128 in 16-bit)
    imm_pattern = r'\$((?:0x[0-9a-fA-F]+)|(?:\d+))'
    matches = re.findall(imm_pattern, clean_line, re.IGNORECASE)
    
    for match in matches:
        try:
            if match.startswith('0x') or match.startswith('0X'):
                # Parse as unsigned, but keep the raw value
                value = int(match, 16)
                # If it looks like a negative value (high bit set), we keep it as is
                # The caller can interpret it as signed if needed
                immediates.append(value)
            else:
                value = int(match, 10)
                immediates.append(value)
        except ValueError:
            pass
    
    return immediates


def find_linear_relationship(v_values: List[int], iv_values: List[int]) -> Optional[Tuple[float, float]]:
    """Find linear relationship IV = a * V + b.
    
    Args:
        v_values: List of source values [V1, V2, V3]
        iv_values: List of immediate values [IV1, IV2, IV3]
    
    Returns:
        (a, b) if linear relationship exists, None otherwise
    """
    if len(v_values) != len(iv_values) or len(v_values) < 2:
        return None
    
    # Remove None values
    valid_pairs = [(v, iv) for v, iv in zip(v_values, iv_values) if v is not None and iv is not None]
    if len(valid_pairs) < 2:
        return None
    
    # Try to find linear relationship: IV = a * V + b
    # With 2 points: solve system of equations
    # IV1 = a * V1 + b
    # IV2 = a * V2 + b
    # a = (IV2 - IV1) / (V2 - V1)
    # b = IV1 - a * V1
    
    if len(valid_pairs) == 2:
        v1, iv1 = valid_pairs[0]
        v2, iv2 = valid_pairs[1]
        
        if v2 == v1:
            return None
        
        a = (iv2 - iv1) / (v2 - v1)
        b = iv1 - a * v1
        
        return (a, b)
    
    # With 3 points: use least squares or check if all satisfy the same line
    if len(valid_pairs) == 3:
        v1, iv1 = valid_pairs[0]
        v2, iv2 = valid_pairs[1]
        v3, iv3 = valid_pairs[2]
        
        # Check if all three points are collinear
        # Calculate a and b from first two points
        if v2 == v1:
            return None
        
        a = (iv2 - iv1) / (v2 - v1)
        b = iv1 - a * v1
        
        # Check if third point satisfies the same line
        expected_iv3 = a * v3 + b
        if abs(expected_iv3 - iv3) < 0.001:  # Allow small floating point error
            return (a, b)
        else:
            return None
    
    return None


def analyze_linear_relationship(prefix: str, v1_file: str, v2_file: str, v3_file: str, 
                                source_values: Dict[str, Tuple[int, int, int]]):
    """Analyze linear relationship between source values and immediate values.
    
    Args:
        prefix: Test group prefix
        v1_file: Path to v1 Basic Block file
        v2_file: Path to v2 Basic Block file
        v3_file: Path to v3 Basic Block file
        source_values: Dictionary of source values
    """
    print(f"\n{'='*80}")
    print(f"Test Group {prefix} - Linear Relationship Analysis")
    print(f"{'='*80}\n")
    
    # Get source values
    if prefix not in source_values:
        print("Error: Could not find source values for this test group")
        return
    
    v1_src, v2_src, v3_src = source_values[prefix]
    
    # Extract immediate values from changed instructions
    def get_immediates_from_file(filepath: str) -> List[int]:
        immediates = []
        with open(filepath, 'r') as f:
            for line in f:
                # Only look at lines with [*] marker (changed instructions)
                if '[*]' in line:
                    imm_vals = extract_immediate_values(line)
                    immediates.extend(imm_vals)
        return immediates
    
    iv1_list = get_immediates_from_file(v1_file)
    iv2_list = get_immediates_from_file(v2_file)
    iv3_list = get_immediates_from_file(v3_file)
    
    print(f"Source values: V1={v1_src}, V2={v2_src}, V3={v3_src}")
    print(f"Immediate values from changed instructions:")
    print(f"  IV1: {iv1_list}")
    print(f"  IV2: {iv2_list}")
    print(f"  IV3: {iv3_list}")
    print()
    
    # Check if we have matching numbers of immediate values
    if not (len(iv1_list) == len(iv2_list) == len(iv3_list) and len(iv1_list) > 0):
        print("Error: Mismatched number of immediate values or no immediate values found")
        print("Cannot determine linear relationship")
        return
    
    # Try to find linear relationship for each immediate value
    v_values = [v1_src, v2_src, v3_src]
    found_relationship = False
    
    for i in range(len(iv1_list)):
        iv1 = iv1_list[i]
        iv2 = iv2_list[i]
        iv3 = iv3_list[i]
        
        print(f"Analyzing immediate value {i+1}:")
        print(f"  IV1={iv1} (0x{iv1:x}), IV2={iv2} (0x{iv2:x}), IV3={iv3} (0x{iv3:x})")
        
        iv_values = [iv1, iv2, iv3]
        
        # Check linear relationship with all three values
        relationship = find_linear_relationship(v_values, iv_values)
        
        if relationship:
            a, b = relationship
            found_relationship = True
            # Format the relationship nicely
            if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
                a_int = int(a)
                b_int = int(b)
                if b_int == 0:
                    print(f"  ✓ Linear relationship found: IV = {a_int} * V")
                elif a_int == 1:
                    print(f"  ✓ Linear relationship found: IV = V + {b_int}")
                elif a_int == -1:
                    print(f"  ✓ Linear relationship found: IV = -V + {b_int}")
                else:
                    print(f"  ✓ Linear relationship found: IV = {a_int} * V + {b_int}")
            else:
                print(f"  ✓ Linear relationship found: IV = {a:.6f} * V + {b:.6f}")
            
            print(f"    Verification:")
            all_match = True
            for v, iv in zip(v_values, iv_values):
                expected = a * v + b
                match = abs(expected - iv) < 0.01
                if not match:
                    all_match = False
                print(f"      V={v}: IV={iv} (0x{iv:x}), Expected={expected:.2f} (0x{int(expected):x}), Match={match}")
            
            if all_match:
                print(f"    ✓ All values match the linear relationship")
        else:
            print(f"  ✗ No linear relationship found")
        print()
    
    if not found_relationship:
        print("Error: No linear relationship found for any immediate value")


def main():
    """Main function."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Extract source values from cmd_v2.sh
    cmd_file = os.path.join(script_dir, 'cmd_v2.sh')
    source_values = extract_source_values(cmd_file)
    
    # Find all *_bb_v1.txt, *_bb_v2.txt, *_bb_v3.txt files
    v1_files = sorted(glob.glob(os.path.join(script_dir, '*_bb_v1.txt')))
    v2_files = sorted(glob.glob(os.path.join(script_dir, '*_bb_v2.txt')))
    v3_files = sorted(glob.glob(os.path.join(script_dir, '*_bb_v3.txt')))
    
    if not v1_files and not v2_files and not v3_files:
        print(f"No *_bb_v1.txt, *_bb_v2.txt, or *_bb_v3.txt files found in {script_dir}")
        return
    
    # Group files by prefix (e.g., "1_bb_v1.txt", "1_bb_v2.txt", "1_bb_v3.txt" -> group "1")
    file_groups = {}
    
    # Process v1 files
    for v1_file in v1_files:
        basename = os.path.basename(v1_file)
        # Extract prefix (e.g., "1" from "1_bb_v1.txt")
        match = re.match(r'^(\d+)_bb_v1\.txt$', basename)
        if match:
            prefix = match.group(1)
            if prefix not in file_groups:
                file_groups[prefix] = {}
            file_groups[prefix]['v1'] = v1_file
    
    # Process v2 files
    for v2_file in v2_files:
        basename = os.path.basename(v2_file)
        match = re.match(r'^(\d+)_bb_v2\.txt$', basename)
        if match:
            prefix = match.group(1)
            if prefix not in file_groups:
                file_groups[prefix] = {}
            file_groups[prefix]['v2'] = v2_file
    
    # Process v3 files
    for v3_file in v3_files:
        basename = os.path.basename(v3_file)
        match = re.match(r'^(\d+)_bb_v3\.txt$', basename)
        if match:
            prefix = match.group(1)
            if prefix not in file_groups:
                file_groups[prefix] = {}
            file_groups[prefix]['v3'] = v3_file
    
    # Sort groups by prefix number
    sorted_groups = sorted(file_groups.items(), key=lambda x: int(x[0]))
    
    print(f"Found {len(sorted_groups)} test group(s)")
    
    # Process each group
    for prefix, files in sorted_groups:
        print(f"\n{'='*80}")
        print(f"Processing Test Group {prefix}")
        print(f"{'='*80}")
        
        seq_v1 = None
        seq_v2 = None
        seq_v3 = None
        
        # Process v1 file (original)
        if 'v1' in files:
            print(f"\n--- Processing v1 (original) ---")
            seq_v1 = process_res_file(files['v1'], return_expressions=True)
        
        # Process v2 file (recompiled from first command)
        if 'v2' in files:
            print(f"\n--- Processing v2 (recompiled from first command) ---")
            seq_v2 = process_res_file(files['v2'], return_expressions=True)
        
        # Process v3 file (recompiled from second command)
        if 'v3' in files:
            print(f"\n--- Processing v3 (recompiled from second command) ---")
            seq_v3 = process_res_file(files['v3'], return_expressions=True)
        
        # Compare expressions
        if seq_v1 and seq_v2:
            print_expression_diff(f"Test Group {prefix}", seq_v1, seq_v2, seq_v3)
        elif seq_v1 and seq_v3:
            print_expression_diff(f"Test Group {prefix}", seq_v1, seq_v3)
        elif seq_v2 and seq_v3:
            print_expression_diff(f"Test Group {prefix}", seq_v2, seq_v3)
        
        # Analyze linear relationship
        if 'v1' in files and 'v2' in files and 'v3' in files:
            analyze_linear_relationship(prefix, files['v1'], files['v2'], files['v3'], source_values)


if __name__ == '__main__':
    main()

