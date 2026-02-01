#!/usr/bin/env python3
"""
Symbolic execution engine for x86 Basic Blocks.
Reads res_*.txt files, parses Basic Blocks, and performs symbolic execution.
"""

import re
import os
import glob
import csv
import json
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
        
        # Alternative symbolic state: for shift instructions, store mul/div version
        # anonymous register -> expression (alternative version)
        self.state_alt: Dict[str, str] = {}
        
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
                        self.state_alt[dst_anon] = src_val  # Same for both versions
                        return f"{dst_anon} = {src_val}"
                    elif src_type == 'reg' and src_reg:
                        # mov %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        src_expr_alt = self.state_alt.get(src_anon, src_expr)
                        self.state[dst_anon] = src_expr
                        self.state_alt[dst_anon] = src_expr_alt  # Copy alternative version too
                        return f"{dst_anon} = {src_expr}"
                    elif src_type == 'mem':
                        # mov [mem], %reg
                        mem_expr = f"mem{src_val}"
                        self.state[dst_anon] = mem_expr
                        self.state_alt[dst_anon] = mem_expr  # Same for both versions
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
                        dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                        new_expr = f"({dst_expr} + {src_val})"
                        new_expr_alt = f"({dst_expr_alt} + {src_val})"
                        self.state[dst_anon] = new_expr
                        self.state_alt[dst_anon] = new_expr_alt
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # add %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        src_expr_alt = self.state_alt.get(src_anon, src_expr)
                        dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                        new_expr = f"({dst_expr} + {src_expr})"
                        new_expr_alt = f"({dst_expr_alt} + {src_expr_alt})"
                        self.state[dst_anon] = new_expr
                        self.state_alt[dst_anon] = new_expr_alt
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
                        dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                        new_expr = f"({dst_expr} - {src_val})"
                        new_expr_alt = f"({dst_expr_alt} - {src_val})"
                        self.state[dst_anon] = new_expr
                        self.state_alt[dst_anon] = new_expr_alt
                        return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # sub %reg1, %reg2
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        src_expr_alt = self.state_alt.get(src_anon, src_expr)
                        dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                        new_expr = f"({dst_expr} - {src_expr})"
                        new_expr_alt = f"({dst_expr_alt} - {src_expr_alt})"
                        self.state[dst_anon] = new_expr
                        self.state_alt[dst_anon] = new_expr_alt
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
                    dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                    
                    if src_type == 'imm':
                        # shl $imm, %reg
                        # Parse shift amount
                        try:
                            if src_val.startswith('0x') or src_val.startswith('0X'):
                                shift_amt = int(src_val, 16)
                            else:
                                shift_amt = int(src_val, 10)
                            
                            # Shift version
                            new_expr = f"({dst_expr} << {src_val})"
                            self.state[dst_anon] = new_expr
                            
                            # Multiplication version: x << n = x * (2^n)
                            multiplier = 2 ** shift_amt
                            new_expr_alt = f"({dst_expr_alt} * {multiplier})"
                            self.state_alt[dst_anon] = new_expr_alt
                            
                            return f"{dst_anon} = {new_expr} (alt: {new_expr_alt})"
                        except (ValueError, TypeError):
                            # If we can't parse the shift amount, just use shift version
                            new_expr = f"({dst_expr} << {src_val})"
                            self.state[dst_anon] = new_expr
                            return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # shl %reg, %reg (variable shift, can't convert to mul)
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} << {src_expr})"
                        self.state[dst_anon] = new_expr
                        # Clear alternative version for variable shifts
                        self.state_alt.pop(dst_anon, None)
                        return f"{dst_anon} = {new_expr}"
        
        # SHR: shr %cl, %reg or shr $imm, %reg
        elif mnemonic_lower == 'shr':
            if len(operands) == 2:
                src_type, src_val, src_reg = self.parse_operand(operands[0])
                dst_type, dst_val, dst_reg = self.parse_operand(operands[1])
                
                if dst_type == 'reg' and dst_reg:
                    dst_anon = self.get_anonymous_reg(dst_reg)
                    dst_expr = self.state.get(dst_anon, dst_anon)
                    dst_expr_alt = self.state_alt.get(dst_anon, dst_expr)
                    
                    if src_type == 'imm':
                        # shr $imm, %reg
                        # Parse shift amount
                        try:
                            if src_val.startswith('0x') or src_val.startswith('0X'):
                                shift_amt = int(src_val, 16)
                            else:
                                shift_amt = int(src_val, 10)
                            
                            # Shift version
                            new_expr = f"({dst_expr} >> {src_val})"
                            self.state[dst_anon] = new_expr
                            
                            # Division version: x >> n = x / (2^n) (integer division)
                            divisor = 2 ** shift_amt
                            new_expr_alt = f"({dst_expr_alt} / {divisor})"
                            self.state_alt[dst_anon] = new_expr_alt
                            
                            return f"{dst_anon} = {new_expr} (alt: {new_expr_alt})"
                        except (ValueError, TypeError):
                            # If we can't parse the shift amount, just use shift version
                            new_expr = f"({dst_expr} >> {src_val})"
                            self.state[dst_anon] = new_expr
                            return f"{dst_anon} = {new_expr}"
                    elif src_type == 'reg' and src_reg:
                        # shr %reg, %reg (variable shift, can't convert to div)
                        src_anon = self.get_anonymous_reg(src_reg)
                        src_expr = self.state.get(src_anon, src_anon)
                        new_expr = f"({dst_expr} >> {src_expr})"
                        self.state[dst_anon] = new_expr
                        # Clear alternative version for variable shifts
                        self.state_alt.pop(dst_anon, None)
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
        """Get all current symbolic expressions (main version)."""
        return dict(self.state)
    
    def get_all_expressions_alt(self) -> Dict[str, str]:
        """Get all current symbolic expressions (alternative version for shifts)."""
        return dict(self.state_alt)
    
    def get_written_effects(self, mnemonic: str, operands: List[str]) -> Tuple[Set[str], Set[str]]:
        """Get written registers and memory locations (effects produced).
        
        Args:
            mnemonic: Instruction mnemonic
            operands: List of operands
        
        Returns:
            Tuple of (written_registers, written_memory) sets
        """
        written_regs = set()
        written_mem = set()
        
        if not operands:
            return (written_regs, written_mem)
        
        mnemonic_lower = mnemonic.lower()
        
        # Instructions that write to destination operand
        if mnemonic_lower in ['mov', 'add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'movzbl', 'sbb']:
            if len(operands) >= 2:
                dst_type, dst_val, dst_reg = self.parse_operand(operands[-1])  # Last operand is usually destination
                if dst_type == 'reg' and dst_reg:
                    base_reg = self.get_base_register(dst_reg)
                    anon_reg = self.get_anonymous_reg(base_reg)
                    written_regs.add(anon_reg)
                elif dst_type == 'mem':
                    written_mem.add(dst_val)
        
        return (written_regs, written_mem)
    
    def get_read_effects(self, mnemonic: str, operands: List[str]) -> Tuple[Set[str], Set[str]]:
        """Get read registers and memory locations (effects consumed).
        
        Args:
            mnemonic: Instruction mnemonic
            operands: List of operands
        
        Returns:
            Tuple of (read_registers, read_memory) sets
        """
        read_regs = set()
        read_mem = set()
        
        if not operands:
            return (read_regs, read_mem)
        
        mnemonic_lower = mnemonic.lower()
        
        # For most instructions, source operands are read
        if mnemonic_lower in ['mov', 'add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'movzbl', 'sbb', 'cmp', 'test']:
            # All operands except the last (destination) are typically read
            for i in range(len(operands) - 1):
                src_type, src_val, src_reg = self.parse_operand(operands[i])
                if src_type == 'reg' and src_reg:
                    base_reg = self.get_base_register(src_reg)
                    anon_reg = self.get_anonymous_reg(base_reg)
                    read_regs.add(anon_reg)
                elif src_type == 'mem':
                    read_mem.add(src_val)
            
            # For cmp/test, both operands are read
            if mnemonic_lower in ['cmp', 'test'] and len(operands) >= 2:
                dst_type, dst_val, dst_reg = self.parse_operand(operands[-1])
                if dst_type == 'reg' and dst_reg:
                    base_reg = self.get_base_register(dst_reg)
                    anon_reg = self.get_anonymous_reg(base_reg)
                    read_regs.add(anon_reg)
                elif dst_type == 'mem':
                    read_mem.add(dst_val)
        
        return (read_regs, read_mem)
    
    def reset(self):
        """Reset the symbolic executor state."""
        self.reg_map.clear()
        self.state.clear()
        self.state_alt.clear()
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
        If return_expressions is True: list of (instruction_line, address, expressions_dict, expressions_dict_alt) tuples
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
    
    expression_sequence = []  # List of (instruction_line, address, expressions_dict, expressions_dict_alt)
    
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
            
            # Get all current expressions (both versions)
            expressions = executor.get_all_expressions()
            expressions_alt = executor.get_all_expressions_alt()
            expressions_dict = dict(sorted(expressions.items()))
            expressions_dict_alt = dict(sorted(expressions_alt.items()))
            
            if return_expressions:
                # Store both versions: (instruction, address, expressions_main, expressions_alt)
                expression_sequence.append((inst_line, address, expressions_dict, expressions_dict_alt))
            
            if expressions:
                print(f"    Expressions after this instruction:")
                for reg, expr in sorted(expressions.items()):
                    alt_expr = expressions_alt.get(reg)
                    if alt_expr and alt_expr != expr:
                        print(f"      {reg} = {expr} (alt: {alt_expr})")
                    else:
                        print(f"      {reg} = {expr}")
            print()
    
    if return_expressions:
        return expression_sequence
    return None


def compare_expressions(seq1: List[Tuple], 
                       seq2: List[Tuple],
                       name1: str = "v1", name2: str = "v2") -> List[Tuple[int, str, str, Dict[str, str], Dict[str, str]]]:
    """Compare two expression sequences and find differences.
    
    Args:
        seq1: First sequence of (instruction, address, expressions, expressions_alt)
        seq2: Second sequence of (instruction, address, expressions, expressions_alt)
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
            if len(seq2[i]) >= 3:
                inst2, addr2, expr2 = seq2[i][:3]
                differences.append((i, None, inst2, {}, expr2))
        elif i >= len(seq2):
            # seq2 ended, seq1 continues
            if len(seq1[i]) >= 3:
                inst1, addr1, expr1 = seq1[i][:3]
                differences.append((i, inst1, None, expr1, {}))
        else:
            # Unpack: (instruction, address, expressions, expressions_alt)
            if len(seq1[i]) >= 3:
                inst1, addr1, expr1 = seq1[i][:3]
            else:
                inst1, addr1, expr1 = seq1[i][0], seq1[i][1] if len(seq1[i]) > 1 else "", {}
            
            if len(seq2[i]) >= 3:
                inst2, addr2, expr2 = seq2[i][:3]
            else:
                inst2, addr2, expr2 = seq2[i][0], seq2[i][1] if len(seq2[i]) > 1 else "", {}
            
            # Compare expressions (use main version for comparison)
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


def get_instruction_effects(inst_line: str, executor: SymbolicExecutor) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """Get written and read effects from an instruction.
    
    Args:
        inst_line: Instruction line
        executor: SymbolicExecutor instance for parsing (will create a temporary one)
    
    Returns:
        Tuple of (written_regs, written_mem, read_regs, read_mem)
    """
    # Create a temporary executor to avoid modifying the original state
    temp_executor = SymbolicExecutor()
    
    clean_line = re.sub(r'^\s*\[\*\]\s*', '', inst_line)
    parsed = temp_executor.parse_instruction(clean_line)
    if not parsed:
        return (set(), set(), set(), set())
    
    address, mnemonic, operands = parsed
    written_regs, written_mem = temp_executor.get_written_effects(mnemonic, operands)
    read_regs, read_mem = temp_executor.get_read_effects(mnemonic, operands)
    
    return (written_regs, written_mem, read_regs, read_mem)


def filter_changed_instructions_by_effects(differences: List[Tuple[int, str, str, Dict[str, str], Dict[str, str]]],
                                           full_sequence: List[Tuple[str, str, Dict[str, str]]],
                                           use_seq1: bool = True) -> List[Tuple[int, str]]:
    """Filter changed instructions until all effects are consumed.
    
    Args:
        differences: List of (index, inst1, inst2, expr1, expr2) tuples
        full_sequence: Full sequence of (instruction, address, expressions)
        use_seq1: If True, use inst1 from differences; otherwise use inst2
    
    Returns:
        List of (index, instruction) tuples for changed instructions to output
    """
    if not differences:
        return []
    
    # Create a temporary executor for parsing (won't modify state)
    temp_executor = SymbolicExecutor()
    pending_effects = set()  # Set of (type, name) where type is 'R' or 'M'
    changed_instructions = []
    
    # Get the starting index of the first changed instruction
    first_changed_idx = differences[0][0]
    
    # Create a map of changed instruction indices
    changed_indices = {diff[0]: diff for diff in differences}
    
    # Process instructions from the first changed instruction onwards
    for i in range(first_changed_idx, len(full_sequence)):
        # Unpack: (instruction, address, expressions, expressions_alt)
        if len(full_sequence[i]) >= 3:
            inst_line, address, expressions = full_sequence[i][:3]
        else:
            inst_line = full_sequence[i][0]
            address = full_sequence[i][1] if len(full_sequence[i]) > 1 else ""
            expressions = {}
        
        # Check if this is a changed instruction
        is_changed = False
        inst_to_use = None
        
        if i in changed_indices:
            diff_idx, inst1, inst2, expr1, expr2 = changed_indices[i]
            is_changed = True
            inst_to_use = inst1 if use_seq1 else inst2
            
            if inst_to_use:
                changed_instructions.append((i + 1, inst_to_use.strip()))
                
                # Get effects produced by this changed instruction
                written_regs, written_mem, read_regs, read_mem = get_instruction_effects(inst_to_use, temp_executor)
                
                # Add written effects to pending list
                for reg in written_regs:
                    pending_effects.add(('R', reg))
                for mem in written_mem:
                    pending_effects.add(('M', mem))
        
        # Get effects consumed by this instruction (use the instruction from sequence)
        written_regs, written_mem, read_regs, read_mem = get_instruction_effects(inst_line, temp_executor)
        
        # Remove consumed effects from pending list
        for reg in read_regs:
            pending_effects.discard(('R', reg))
        for mem in read_mem:
            pending_effects.discard(('M', mem))
        
        # If all effects are consumed and we've processed at least one changed instruction, stop
        if is_changed and not pending_effects and changed_instructions:
            break
    
    return changed_instructions


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
        
        # Filter changed instructions until all effects are consumed
        changed_v1 = filter_changed_instructions_by_effects(diff_v1_v2, seq1, use_seq1=True)
        changed_v2 = filter_changed_instructions_by_effects(diff_v1_v2, seq2, use_seq1=False)
        
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
            
            # Filter changed instructions until all effects are consumed
            changed_v2 = filter_changed_instructions_by_effects(diff_v2_v3, seq2, use_seq1=True)
            changed_v3 = filter_changed_instructions_by_effects(diff_v2_v3, seq3, use_seq1=False)
            
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
            
            # Filter changed instructions until all effects are consumed
            changed_v1 = filter_changed_instructions_by_effects(diff_v1_v3, seq1, use_seq1=True)
            changed_v3 = filter_changed_instructions_by_effects(diff_v1_v3, seq3, use_seq1=False)
            
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
    
    # Find first non-comment line that matches "num,num,num" pattern
    v1, v2, v3 = None, None, None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Check if line matches "num,num,num" pattern
        match = re.match(r'^(\d+),(\d+),(\d+)$', line)
        if match:
            try:
                v1 = int(match.group(1))
                v2 = int(match.group(2))
                v3 = int(match.group(3))
                break
            except ValueError:
                continue
    
    if v1 is None or v2 is None or v3 is None:
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


def extract_file_paths(cmd_file: str) -> Dict[str, str]:
    """Extract file paths from cmd_v2.sh commands.
    
    Args:
        cmd_file: Path to cmd_v2.sh
    
    Returns:
        Dictionary mapping test group prefix to file path
    """
    file_paths = {}
    
    if not os.path.exists(cmd_file):
        return file_paths
    
    with open(cmd_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return file_paths
    
    # Find commands and extract -f parameter
    test_group = 1
    cmd_count = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Skip V1,V2,V3 lines
        if re.match(r'^\d+,\d+,\d+$', line):
            continue
        
        # Check if it's a command line with -f parameter
        if 'check_assembly_diff.py' in line and '-f' in line:
            # Extract file path from -f parameter
            # Pattern: -f path/to/file.c
            match = re.search(r'-f\s+(\S+)', line)
            if match:
                file_path = match.group(1)
                cmd_count += 1
                if cmd_count == 1:
                    # First command of a test group
                    file_paths[str(test_group)] = file_path
                elif cmd_count == 2:
                    # Second command of a test group, verify it's the same file
                    if str(test_group) in file_paths and file_paths[str(test_group)] != file_path:
                        print(f"Warning: Test group {test_group} has different file paths")
                    test_group += 1
                    cmd_count = 0
    
    return file_paths


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

    # Handle implicit immediate of 1 for shift/rotate instructions
    # In x86, instructions like "shr %eax" implicitly shift by 1
    # These instructions are: shr, shl, sar, sal, rol, ror, rcl, rcr
    if not immediates:
        # Extract the mnemonic from the instruction
        # Format: "addr: bytes mnemonic operands"
        mnemonic_match = re.search(r'\t(\w+)\s+', clean_line)
        if mnemonic_match:
            mnemonic = mnemonic_match.group(1).lower()
            # Check if it's a shift/rotate instruction with implicit immediate 1
            shift_rotate_ops = {'shr', 'shl', 'sar', 'sal', 'rol', 'ror', 'rcl', 'rcr'}
            if mnemonic in shift_rotate_ops:
                # Check if operand is just a register (no explicit immediate)
                # Pattern: mnemonic %reg (without $imm)
                operand_match = re.search(r'\t\w+\s+(%\w+)\s*$', clean_line)
                if operand_match:
                    # This is a shift/rotate with implicit immediate 1
                    immediates.append(1)

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


def find_insertion_point_for_linear_relationship(differences: List[Tuple[int, str, str, Dict[str, str], Dict[str, str]]],
                                                  full_sequence: List[Tuple],
                                                  relationship: Tuple[float, float]) -> Optional[Tuple[int, str, str, str, str]]:
    """Find where to insert an instruction to modify R/M value based on linear relationship.
    
    Args:
        differences: List of (index, inst1, inst2, expr1, expr2) tuples
        full_sequence: Full sequence of (instruction, address, expressions, expressions_alt)
        relationship: (a, b) tuple representing IV = a * V + b
    
    Returns:
        Tuple of (insertion_index, effect_type, effect_name, first_inst, actual_reg_name) or None
        effect_type is 'R' for register or 'M' for memory
        actual_reg_name is the actual register name from the instruction (e.g., "eax")
    """
    if not differences:
        return None
    
    temp_executor = SymbolicExecutor()
    
    # Get the first changed instruction
    first_diff = differences[0]
    first_idx = first_diff[0]
    first_inst = first_diff[1]  # Use inst1 (from v1)
    
    if not first_inst:
        return None
    
    # Get effects produced by the first changed instruction
    written_regs, written_mem, read_regs, read_mem = get_instruction_effects(first_inst, temp_executor)
    
    if not written_regs and not written_mem:
        return None
    
    # Find the first consumption of these effects
    # We need to find where the first written reg/mem is consumed
    target_effect = None
    target_type = None
    target_name = None
    actual_reg_name = None
    
    # Parse the first instruction to get the actual register name
    parsed = temp_executor.parse_instruction(first_inst)
    if parsed:
        address, mnemonic, operands = parsed
        # Usually the destination operand is the last one
        if operands and len(operands) >= 2:
            dst_operand = operands[-1]
            # Extract register name from operand (e.g., "%eax" -> "eax")
            if dst_operand.startswith('%'):
                actual_reg_name = dst_operand[1:]
                # Get base register for anonymous name
                base_reg = temp_executor.get_base_register(actual_reg_name)
                target_name = base_reg
    
    # Prefer register over memory (usually easier to modify)
    if written_regs:
        target_effect = list(written_regs)[0]
        target_type = 'R'
        if not target_name:
            target_name = target_effect
    elif written_mem:
        target_effect = list(written_mem)[0]
        target_type = 'M'
        if not target_name:
            target_name = target_effect
    
    if not target_effect:
        return None
    
    # Find where this effect is first consumed
    insertion_idx = None
    for i in range(first_idx + 1, len(full_sequence)):
        inst_line = full_sequence[i][0] if len(full_sequence[i]) > 0 else ""
        written_regs_curr, written_mem_curr, read_regs_curr, read_mem_curr = get_instruction_effects(inst_line, temp_executor)
        
        # Check if this instruction consumes our target effect
        if target_type == 'R' and target_effect in read_regs_curr:
            insertion_idx = i
            break
        elif target_type == 'M' and target_effect in read_mem_curr:
            insertion_idx = i
            break
    
    if insertion_idx is None:
        # If not found, insert right after the first changed instruction
        insertion_idx = first_idx + 1
    
    return (insertion_idx, target_type, target_name, first_inst, actual_reg_name or target_name)


def generate_insertion_instruction(target_type: str, target_name: str, a: float, b: float, 
                                   new_value_name: str = "X") -> str:
    """Generate an instruction to modify R/M value based on linear relationship.
    
    Args:
        target_type: 'R' for register or 'M' for memory
        target_name: Name of register or memory location
        a: Coefficient in IV = a * V + b
        b: Constant in IV = a * V + b
        new_value_name: Name of the new source value (default: "X")
    
    Returns:
        Suggested instruction as string
    """
    # Calculate the new immediate value: a * X + b
    # Since we don't know X, we'll generate a symbolic instruction
    if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
        a_int = int(a)
        b_int = int(b)
        
        if target_type == 'R':
            # Generate mov instruction: mov $imm, %reg
            if b_int == 0:
                if a_int == 1:
                    # IV = X, so we need to set reg to X
                    # This is tricky - we'd need the actual value of X
                    # For now, generate a placeholder
                    return f"mov ${new_value_name}, %{target_name}  # Set {target_name} = {new_value_name}"
                else:
                    # IV = a * X, need to multiply
                    return f"# To set {target_name} = {a_int} * {new_value_name}:\n" \
                           f"#   mov ${new_value_name}, %{target_name}\n" \
                           f"#   imul ${a_int}, %{target_name}"
            elif a_int == 1:
                # IV = X + b
                return f"# To set {target_name} = {new_value_name} + {b_int}:\n" \
                       f"#   mov ${new_value_name}, %{target_name}\n" \
                       f"#   add ${b_int}, %{target_name}"
            elif a_int == -1:
                # IV = -X + b
                return f"# To set {target_name} = -{new_value_name} + {b_int}:\n" \
                       f"#   mov ${new_value_name}, %{target_name}\n" \
                       f"#   neg %{target_name}\n" \
                       f"#   add ${b_int}, %{target_name}"
            else:
                # IV = a * X + b
                return f"# To set {target_name} = {a_int} * {new_value_name} + {b_int}:\n" \
                       f"#   mov ${new_value_name}, %{target_name}\n" \
                       f"#   imul ${a_int}, %{target_name}\n" \
                       f"#   add ${b_int}, %{target_name}"
        else:
            # Memory - similar logic but with memory addressing
            return f"# To modify memory {target_name} = {a_int} * {new_value_name} + {b_int}"
    else:
        # Non-integer coefficients - more complex
        return f"# To set {target_name} = {a:.6f} * {new_value_name} + {b:.6f} (non-integer, complex calculation needed)"


def analyze_linear_relationship(prefix: str, v1_file: str, v2_file: str, v3_file: str, 
                                source_values: Dict[str, Tuple[int, int, int]],
                                seq1: List[Tuple] = None, diff_v1_v2: List[Tuple] = None,
                                file_path: str = None, output_dir: str = None):
    """Analyze linear relationship between source values and immediate values.
    
    Args:
        prefix: Test group prefix
        v1_file: Path to v1 Basic Block file
        v2_file: Path to v2 Basic Block file
        v3_file: Path to v3 Basic Block file
        source_values: Dictionary of source values
        seq1: v1 sequence (optional, for finding insertion point)
        diff_v1_v2: Differences between v1 and v2 (optional, for finding insertion point)
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
            
            # Format the relationship string for display and storage
            if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
                a_int = int(a)
                b_int = int(b)
                if b_int == 0:
                    rel_str = f"IV = {a_int} * V" if a_int != 1 else "IV = V"
                    if a_int == -1:
                        rel_str = "IV = -V"
                elif a_int == 1:
                    rel_str = f"IV = V + {b_int}"
                elif a_int == -1:
                    rel_str = f"IV = -V + {b_int}"
                else:
                    rel_str = f"IV = {a_int} * V + {b_int}"
            else:
                rel_str = f"IV = {a:.6f} * V + {b:.6f}"
            
            # Format the relationship nicely for display
            print(f"  ✓ Linear relationship found: {rel_str}")
            
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
            
            # Generate insertion instruction suggestion
            if seq1 and diff_v1_v2:
                insertion_info = find_insertion_point_for_linear_relationship(diff_v1_v2, seq1, relationship)
                if insertion_info:
                    insertion_idx, target_type, target_name, first_inst, actual_reg_name = insertion_info
                    print(f"\n    {'─'*70}")
                    print(f"    Insertion Point Analysis")
                    print(f"    {'─'*70}")
                    
                    # Clean up the first instruction line for better readability
                    clean_first_inst = first_inst.strip()
                    if clean_first_inst.startswith('[*]'):
                        clean_first_inst = clean_first_inst[3:].strip()
                    
                    print(f"    First changed instruction:")
                    print(f"      {clean_first_inst}")
                    print()
                    print(f"    Target register: %{actual_reg_name}")
                    if actual_reg_name != target_name:
                        print(f"      (64-bit base: %{target_name})")
                    print()
                    print(f"    Insert position: Before instruction {insertion_idx + 1}")
                    print()
                    
                    # Generate suggested instruction
                    suggested_inst = generate_insertion_instruction(target_type, actual_reg_name, a, b)
                    print(f"    Suggested instruction to insert:")
                    print(f"    {'─'*70}")
                    for line in suggested_inst.split('\n'):
                        if line.strip():
                            print(f"      {line}")
                    print(f"    {'─'*70}")
                    
                    # Get changed instructions for CS field
                    changed_v1_instructions = filter_changed_instructions_by_effects(diff_v1_v2, seq1, use_seq1=True)
                    # Format CS as a semicolon-separated list of instructions
                    cs_instructions = []
                    for idx, inst in changed_v1_instructions:
                        # Clean up instruction: remove [*] marker and normalize whitespace
                        clean_inst = inst.strip()
                        if clean_inst.startswith('[*]'):
                            clean_inst = clean_inst[3:].strip()
                        # Normalize whitespace: replace multiple spaces/tabs with single space
                        clean_inst = re.sub(r'\s+', ' ', clean_inst)
                        cs_instructions.append(clean_inst)
                    cs_info = "; ".join(cs_instructions) if cs_instructions else first_inst.strip()
                    
                    # Generate BPF file
                    result = generate_bpf_file_for_group(prefix, v1_file, relationship, actual_reg_name, insertion_info, file_path, output_dir)
                    if result:
                        internal_file, user_policy_file = result
                        print(f"\n    Generated BPF file: {internal_file}")
                        if user_policy_file:
                            print(f"    Generated user policy file: {user_policy_file}")
                        
                        # Extract BPF file name (e.g., "my_policy_1.bpf.c" -> "my_policy_1.bpf.o")
                        bpf_file_name = ""
                        if user_policy_file:
                            # Get just the filename without path
                            bpf_base_name = os.path.basename(user_policy_file)
                            # Change extension from .bpf.c to .bpf.o
                            if bpf_base_name.endswith('.bpf.c'):
                                bpf_file_name = bpf_base_name[:-6] + '.bpf.o'
                            else:
                                bpf_file_name = bpf_base_name
                        
                        # Add entry to Scope Table
                        # Build SS (Symbolic State) from expression
                        # Create expr_comment from rel_str by replacing IV with target_reg and V with val
                        # Example: "IV = V" -> "eax = val", then format as "eax=val"
                        expr_comment_local = rel_str.replace('IV', actual_reg_name).replace('V', 'val')
                        # Extract the right-hand side of the equation for SS
                        # If format is "eax = val", extract "val"
                        if ' = ' in expr_comment_local:
                            rhs = expr_comment_local.split(' = ', 1)[1]
                            ss_info = f"{actual_reg_name}={rhs}"
                        else:
                            ss_info = f"{actual_reg_name}={expr_comment_local}"
                        
                        # Use source value V1 as Val
                        # ConstID is uint64_t, use prefix as numeric value
                        try:
                            const_id_value = int(prefix)
                        except ValueError:
                            const_id_value = 0
                        
                        add_scope_table_entry(
                            const_id=str(const_id_value),
                            val=v1_src,
                            expression=rel_str,
                            cs_content=cs_info,
                            ss_content=ss_info,
                            bpf_file=bpf_file_name,
                            status="active"
                        )
                        print(f"    Added entry to Scope Table: ConstID={const_id_value}, V={v1_src}, {rel_str}")
        else:
            print(f"  ✗ No linear relationship found")
        print()
    
    if not found_relationship:
        print("Error: No linear relationship found for any immediate value")


SCOPE_TABLE_PATH = "/dev/shm/xkernel/scope_table"
CS_TABLE_PATH = "/dev/shm/xkernel/cs_table"
SS_TABLE_PATH = "/dev/shm/xkernel/ss_table"

SCOPE_TABLE_HEADER = ["ConstID", "Val", "Expression", "CS_Index", "SS_Index", "BPF_File", "Status"]
CS_TABLE_HEADER = ["Index", "CS_Content"]
SS_TABLE_HEADER = ["Index", "SS_Content"]


def init_table(table_path: str, header: List[str]):
    """Initialize a table file if it doesn't exist.
    
    Args:
        table_path: Path to the table file
        header: List of column names
    """
    # Create directory if it doesn't exist
    table_dir = os.path.dirname(table_path)
    if table_dir and not os.path.exists(table_dir):
        os.makedirs(table_dir, exist_ok=True)
    
    # Create file with header if it doesn't exist
    if not os.path.exists(table_path):
        with open(table_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(header)


def init_all_tables():
    """Initialize all tables (Scope, CS, SS) if they don't exist."""
    init_table(SCOPE_TABLE_PATH, SCOPE_TABLE_HEADER)
    init_table(CS_TABLE_PATH, CS_TABLE_HEADER)
    init_table(SS_TABLE_PATH, SS_TABLE_HEADER)


def get_or_add_cs_index(cs_content: str) -> int:
    """Get existing CS index or add new CS entry and return its index.
    
    Args:
        cs_content: CS content (instruction string)
    
    Returns:
        Index of the CS entry
    """
    init_table(CS_TABLE_PATH, CS_TABLE_HEADER)
    
    # Read existing entries
    entries = []
    max_index = 0
    if os.path.exists(CS_TABLE_PATH):
        with open(CS_TABLE_PATH, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None)
            if header:
                for row in reader:
                    if len(row) >= 2:
                        index = int(row[0])
                        content = row[1]
                        entries.append((index, content))
                        max_index = max(max_index, index)
                        # Check if this content already exists
                        if content == cs_content:
                            return index
    
    # Add new entry
    new_index = max_index + 1
    entries.append((new_index, cs_content))
    
    # Write back
    with open(CS_TABLE_PATH, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(CS_TABLE_HEADER)
        for index, content in sorted(entries):
            writer.writerow([index, content])
    
    return new_index


def get_or_add_ss_index(ss_content: str) -> int:
    """Get existing SS index or add new SS entry and return its index.
    
    Args:
        ss_content: SS content (symbolic state string)
    
    Returns:
        Index of the SS entry
    """
    init_table(SS_TABLE_PATH, SS_TABLE_HEADER)
    
    # Read existing entries
    entries = []
    max_index = 0
    if os.path.exists(SS_TABLE_PATH):
        with open(SS_TABLE_PATH, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None)
            if header:
                for row in reader:
                    if len(row) >= 2:
                        index = int(row[0])
                        content = row[1]
                        entries.append((index, content))
                        max_index = max(max_index, index)
                        # Check if this content already exists
                        if content == ss_content:
                            return index
    
    # Add new entry
    new_index = max_index + 1
    entries.append((new_index, ss_content))
    
    # Write back
    with open(SS_TABLE_PATH, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(SS_TABLE_HEADER)
        for index, content in sorted(entries):
            writer.writerow([index, content])
    
    return new_index


def add_scope_table_entry(const_id: str, val: int, expression: str, cs_content: str, ss_content: str, bpf_file: str = "", status: str = "active"):
    """Add a new entry to the Scope Table.
    
    Args:
        const_id: Constant ID as uint64_t (numeric string, e.g., "1", "2")
        val: Source value V
        expression: Linear relationship expression (e.g., "IV = V" or "IV = a * V + b")
        cs_content: CS content (instruction string)
        ss_content: SS content (symbolic state string) - currently not used, set to empty string
        bpf_file: BPF file name (e.g., "my_policy_1.bpf.o")
        status: Status of the entry (default: "active")
    """
    init_all_tables()
    
    # Get or add CS index
    cs_index = get_or_add_cs_index(cs_content)
    # Temporarily not generating SS, use empty string for SS_Index
    ss_index = ""
    
    # Read existing entries to avoid duplicates
    existing_entries = []
    if os.path.exists(SCOPE_TABLE_PATH):
        with open(SCOPE_TABLE_PATH, 'r', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None)
            if header:
                existing_entries = list(reader)
    
    # Check if entry already exists (same ConstID and Val)
    for entry in existing_entries:
        if len(entry) >= 2 and entry[0] == const_id and entry[1] == str(val):
            # Update existing entry
            entry[2] = expression
            entry[3] = str(cs_index)
            entry[4] = str(ss_index)
            entry[5] = bpf_file if len(entry) > 5 else bpf_file
            entry[6] = status if len(entry) > 6 else status
            # Write back
            with open(SCOPE_TABLE_PATH, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(SCOPE_TABLE_HEADER)
                writer.writerows(existing_entries)
            return
    
    # Add new entry
    new_entry = [const_id, str(val), expression, str(cs_index), str(ss_index), bpf_file, status]
    with open(SCOPE_TABLE_PATH, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(new_entry)


def extract_function_info_from_bb_file(filepath: str) -> Optional[Tuple[str, str, str, str]]:
    """Extract function name, first instruction address, changed instruction address, and kprobe offset address from BB file.
    
    Args:
        filepath: Path to *_bb_v1.txt file
    
    Returns:
        Tuple of (function_name, first_addr, changed_addr, kprobe_addr) or None
        kprobe_addr is the address of the instruction after changed instruction (for kprobe attachment)
    """
    if not os.path.exists(filepath):
        return None
    
    function_name = None
    first_addr = None
    changed_addr = None
    kprobe_addr = None
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        found_changed = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Extract function name
            if line.startswith('Function:'):
                func_match = re.match(r'^Function:\s+(.+)$', line)
                if func_match:
                    function_name = func_match.group(1)
            
            # Extract first instruction address (first non-empty instruction line)
            if not first_addr and re.match(r'^\s*([0-9a-fA-F]+):', line):
                match = re.match(r'^\s*([0-9a-fA-F]+):', line)
                if match:
                    first_addr = match.group(1)
            
            # Extract changed instruction address (line with [*])
            if '[*]' in line and not found_changed:
                match = re.match(r'^\s*\[\*\]\s*([0-9a-fA-F]+):', line)
                if match:
                    changed_addr = match.group(1)
                    found_changed = True
                    
                    # Get the next instruction address (for kprobe offset)
                    # kprobe executes before the attached instruction, so we attach to the instruction after changed
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Look for next instruction address
                        next_match = re.match(r'^\s*([0-9a-fA-F]+):', next_line)
                        if next_match:
                            kprobe_addr = next_match.group(1)
                            break
                    break
    
    if function_name and first_addr and changed_addr and kprobe_addr:
        return (function_name, first_addr, changed_addr, kprobe_addr)
    return None


def generate_bpf_user_policy_file(prefix: str, function_name: str, file_path: str, 
                                  offset: int) -> str:
    """Generate BPF user policy file with X_TUNE macro.
    
    Args:
        prefix: Test group prefix
        function_name: Function name
        file_path: Source file path
        offset: Kprobe offset (hex value like 0x22a)
    
    Returns:
        Generated BPF code as string
    """
    # Extract offset from location string format
    # Format should be "+0x<offset>" for SEC("kprobe/function+0x<offset>")
    location_str = f'"+0x{offset:x}"'
    
    # location_str is now "+0x<offset>", but X_TUNE expects the full location string
    # We need to pass the location string that includes file path for documentation
    # But the SEC() macro only needs the offset part
    location_str_for_sec = f'"+0x{offset:x}"'
    location_str_for_comment = f'"{file_path}:L<line>:<col>:0x{offset:x}"'
    
    bpf_code = f"""#include "my_policy_{prefix}.internal.bpf.h"

X_TUNE({function_name}, {location_str_for_sec}) {{
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;
    // 2. User policy logic
    // TODO: Implement your policy logic here
    return 0;
}} /* my_policy_{prefix}.bpf.c */
"""
    return bpf_code


def generate_bpf_kprobe_file(prefix: str, v1_file: str, relationship: Tuple[float, float],
                             target_reg: str, insertion_info: Tuple) -> Optional[str]:
    """Generate BPF kprobe file based on analysis results.
    
    Args:
        prefix: Test group prefix (e.g., "1")
        v1_file: Path to v1 Basic Block file
        relationship: (a, b) tuple representing IV = a * V + b
        target_reg: Target register name (e.g., "eax")
        insertion_info: Tuple from find_insertion_point_for_linear_relationship
    
    Returns:
        Generated BPF code as string or None
    """
    # Extract function info
    func_info = extract_function_info_from_bb_file(v1_file)
    if not func_info:
        return None
    
    function_name, first_addr, changed_addr, kprobe_addr = func_info
    
    # kprobe_addr is already the offset (e.g., "22a" means offset 0x22a)
    # kprobe executes before the attached instruction, so we attach to the instruction after changed
    try:
        offset = int(kprobe_addr, 16)
    except ValueError:
        return None
    
    a, b = relationship
    
    # Generate helper function name
    helper_name = f"impl_sie_logic_cs{prefix}"
    kprobe_name = f"impl_cs_{prefix}"
    
    # Map register names to pt_regs field names
    reg_to_ptregs = {
        'rax': 'ax', 'rbx': 'bx', 'rcx': 'cx', 'rdx': 'dx',
        'rsi': 'si', 'rdi': 'di', 'rbp': 'bp', 'rsp': 'sp',
        'r8': 'r8', 'r9': 'r9', 'r10': 'r10', 'r11': 'r11',
        'r12': 'r12', 'r13': 'r13', 'r14': 'r14', 'r15': 'r15',
        'eax': 'ax', 'ebx': 'bx', 'ecx': 'cx', 'edx': 'dx',
        'esi': 'si', 'edi': 'di', 'ebp': 'bp', 'esp': 'sp',
    }
    
    # Get base register
    base_reg = target_reg
    if target_reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']:
        # Map 32-bit to 64-bit
        reg32_to_64 = {
            'eax': 'rax', 'ebx': 'rbx', 'ecx': 'rcx', 'edx': 'rdx',
            'esi': 'rsi', 'edi': 'rdi', 'ebp': 'rbp', 'esp': 'rsp',
        }
        base_reg = reg32_to_64.get(target_reg, target_reg)
    
    ptregs_field = reg_to_ptregs.get(base_reg, base_reg)
    
    # Generate the expression for new value
    # IV = a * V + b, where V is the parameter
    if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
        a_int = int(a)
        b_int = int(b)
        
        if b_int == 0:
            if a_int == 1:
                expr = "val"
            elif a_int == -1:
                expr = "-val"
            else:
                expr = f"(val * {a_int})"
        elif a_int == 1:
            expr = f"(val + {b_int})"
        elif a_int == -1:
            expr = f"(-val + {b_int})"
        else:
            expr = f"((val * {a_int}) + {b_int})"
    else:
        # Non-integer coefficients - use floating point (may need adjustment)
        expr = f"((val * {a:.6f}) + {b:.6f})"
    
    # Format relationship string for comments
    if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
        a_int = int(a)
        b_int = int(b)
        if b_int == 0:
            if a_int == 1:
                rel_str = "IV = V"
            elif a_int == -1:
                rel_str = "IV = -V"
            else:
                rel_str = f"IV = {a_int} * V"
        elif a_int == 1:
            rel_str = f"IV = V + {b_int}"
        elif a_int == -1:
            rel_str = f"IV = -V + {b_int}"
        else:
            rel_str = f"IV = {a_int} * V + {b_int}"
    else:
        rel_str = f"IV = {a:.6f} * V + {b:.6f}"
    
    # Format relationship string for comments
    if abs(a - int(a)) < 0.001 and abs(b - int(b)) < 0.001:
        a_int = int(a)
        b_int = int(b)
        if b_int == 0:
            if a_int == 1:
                rel_str = "IV = V"
            elif a_int == -1:
                rel_str = "IV = -V"
            else:
                rel_str = f"IV = {a_int} * V"
        elif a_int == 1:
            rel_str = f"IV = V + {b_int}"
        elif a_int == -1:
            rel_str = f"IV = -V + {b_int}"
        else:
            rel_str = f"IV = {a_int} * V + {b_int}"
    else:
        rel_str = f"IV = {a:.6f} * V + {b:.6f}"
    
    # Generate comment for expression (replace IV with target_reg, V with val)
    expr_comment = rel_str.replace('IV', target_reg).replace('V', 'val')
    
    # Generate BPF header code
    bpf_code = f"""// Generated BPF kprobe header for test group {prefix}
// Function: {function_name}
// Offset: 0x{offset:X} (changed instruction at 0x{changed_addr}, kprobe attach at offset 0x{kprobe_addr})
// Linear relationship: {rel_str}
// Target register: %{target_reg} (base: %{base_reg})

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// 1. Helper: SIE Indirection
static __always_inline void {helper_name}(
    struct pt_regs *regs, u64 val) {{
    // Recovered symbolic state expression
    // {expr_comment}
    u64 new_{ptregs_field} = {expr};
    
    // Writing back to pt_regs using the kfunc
    sie_write_kernel(&regs->{ptregs_field}, sizeof(regs->{ptregs_field}), &new_{ptregs_field});
}}

// 2. X_TUNE macro: wraps BPF_KPROBE and calls user policy
// Usage: X_TUNE(function_name, "file_path:L<line>:<col>:0x<offset>") {{ ... }}
// The macro expands to:
//   - A forward declaration of __user_policy_<func_name>
//   - A BPF_KPROBE function that sets up x_ctx and calls __user_policy_<func_name>
//   - The actual __user_policy_<func_name> function definition (user provides body)
#define X_TUNE(func_name, location_str) \\
    static int __user_policy_##func_name(struct x_ctx *x_ctx, struct pt_regs *ctx); \\
    SEC("kprobe/" #func_name location_str) \\
    int BPF_KPROBE(impl_cs_{prefix}) {{ \\
        struct x_ctx x_ctx_local = {{ \\
            .regs = ctx, \\
            .set_fn = &{helper_name}, \\
        }}; \\
        return __user_policy_##func_name(&x_ctx_local, ctx); \\
    }} \\
    static int __user_policy_##func_name(struct x_ctx *x_ctx, struct pt_regs *ctx)
"""
    # Note: This generates my_policy_{prefix}.internal.bpf.h
    
    return bpf_code


def generate_bpf_file_for_group(prefix: str, v1_file: str, relationship: Optional[Tuple[float, float]],
                                target_reg: str, insertion_info: Optional[Tuple],
                                file_path: str = None, output_dir: str = None) -> Optional[Tuple[str, str]]:
    """Generate BPF kprobe files for a test group.
    
    Args:
        prefix: Test group prefix
        v1_file: Path to v1 Basic Block file
        relationship: Linear relationship (a, b) or None
        target_reg: Target register name
        insertion_info: Insertion point info or None
        file_path: Source file path (for user policy file)
        output_dir: Output directory (default: same as v1_file directory)
    
    Returns:
        Tuple of (internal_file_path, user_policy_file_path) or None
    """
    if not relationship or not insertion_info:
        return None
    
    bpf_code = generate_bpf_kprobe_file(prefix, v1_file, relationship, target_reg, insertion_info)
    if not bpf_code:
        return None
    
    # Determine output path
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(v1_file))
    
    # Write internal BPF header file
    internal_file = os.path.join(output_dir, f"my_policy_{prefix}.internal.bpf.h")
    with open(internal_file, 'w') as f:
        f.write(bpf_code)
    
    # Generate and write user policy BPF file
    if file_path:
        func_info = extract_function_info_from_bb_file(v1_file)
        if func_info:
            function_name, first_addr, changed_addr, kprobe_addr = func_info
            try:
                offset = int(kprobe_addr, 16)
                user_policy_code = generate_bpf_user_policy_file(prefix, function_name, file_path, offset)
                user_policy_file = os.path.join(output_dir, f"my_policy_{prefix}.bpf.c")
                with open(user_policy_file, 'w') as f:
                    f.write(user_policy_code)
                return (internal_file, user_policy_file)
            except ValueError:
                pass
    
    return (internal_file, None)


def main():
    """Main function."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine output directory for BPF files (bpf_kprobe/bpf/examples/)
    project_root = os.path.dirname(script_dir)  # Go up from UnitTestsCS to Xkernel
    bpf_output_dir = os.path.join(project_root, 'bpf_kprobe', 'bpf', 'examples')
    os.makedirs(bpf_output_dir, exist_ok=True)
    
    # Extract source values and file paths from cmd_v2.sh
    cmd_file = os.path.join(script_dir, 'cmd_v2.sh')
    source_values = extract_source_values(cmd_file)
    file_paths = extract_file_paths(cmd_file)
    
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
            # Get differences between v1 and v2 for insertion point analysis
            diff_v1_v2_for_insertion = None
            if seq_v1 and seq_v2:
                diff_v1_v2_for_insertion = compare_expressions(seq_v1, seq_v2, "v1", "v2")
            
            file_path = file_paths.get(prefix)
            analyze_linear_relationship(prefix, files['v1'], files['v2'], files['v3'], 
                                      source_values, seq_v1, diff_v1_v2_for_insertion, file_path, bpf_output_dir)


if __name__ == '__main__':
    main()

