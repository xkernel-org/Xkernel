import re
def parse_instructions(instructions_txt):
    """
    Given the contents of Instructions.txt and a number indicating which line,
    extract the instructions at that line as objects:
    - Each instruction object has: opcode, operand1, operand2
    - Only keep the instruction after the address and bytes, i.e. keep things like 'add $0x40,%eax'
    - For each instruction, split into opcode and up to 2 operands

    Returns a list of Instruction objects
    """
    lines = instructions_txt.strip().splitlines()

    # File content format: need to extract instruction part from each line, e.g., input:
    # cf:	41 80 fd 01          	cmp    $0x1,%r13b
    # d3:	19 c0                	sbb    %eax,%eax
    # d5:	83 e0 e0             	and    $0xffffffe0,%eax
    # d8:	83 c0 40             	add    $0x40,%eax
    # Output:
    # ['cmp $0x1,%r13b', 'sbb %eax,%eax', 'and $0xffffffe0,%eax', 'add $0x40,%eax']
    # Then represent each instruction as an Instruction object, storing opcode, operand1, operand2.
    class Instruction:
        def __init__(self, opcode, operand1, operand2):
            self.opcode = opcode
            self.operand1 = operand1
            self.operand2 = operand2    
        def __str__(self):
            def format_operand(op):
                if op is None:
                    return ""
                # If operand is an integer (immediate value), format as hex with $ prefix
                if isinstance(op, int):
                    return f"$0x{op:x}"
                # Otherwise, return as string (register names, etc.)
                return str(op)
            
            op1_str = format_operand(self.operand1)
            op2_str = format_operand(self.operand2)
            
            # Build output string, only include non-empty operands
            parts = [self.opcode]
            if op1_str:
                parts.append(op1_str)
            if op2_str:
                parts.append(op2_str)
            return " ".join(parts)
    instructions = []
    for line in lines:
        # Parse format: '  cf:	41 80 fd 01          	cmp    $0x1,%r13b'
        # Pattern: address: hex_bytes(tab-separated) instruction
        # Match address: followed by hex bytes (pairs of hex digits), then instruction
        # Hex bytes are separated by spaces and end with tab or multiple spaces
        m = re.match(r'\s*[0-9a-f]+:\s+((?:[0-9a-f]{2}\s*)+)\s+(.+)', line)
        if not m:
            continue
        # Extract instruction part (everything after the hex bytes)
        instruction_text = m.group(2).strip()
        if not instruction_text:
            continue
        
        # Split instruction into opcode and operands
        parts = instruction_text.split()
        if len(parts) == 0:
            continue
        
        opcode = parts[0]
        # The rest is operands
        operands = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Parse immediate values (starting with $) as integers
        def parse_operand(op_str):
            if not op_str:
                return None
            op_str = op_str.strip()
            # If starts with $, it's an immediate value
            if op_str.startswith('$'):
                # Remove $ and parse as integer
                value_str = op_str[1:]
                # Handle hex format (0x...)
                if value_str.startswith('0x'):
                    # Parse as unsigned first, then convert to signed if needed
                    return int(value_str, 16)
                # Handle decimal format
                elif value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                    return int(value_str, 10)
                else:
                    # If can't parse, return as string
                    return op_str
            # Otherwise, return as string (register names, etc.)
            return op_str
        
        def split_operands(operands_str):
            """
            Split operands string into operand1 and operand2.
            Handles complex address expressions like (%rdx,%rdx,4) correctly.
            For 3-operand instructions like imul $imm, src, dst, we combine src,dst as operand2.
            """
            if not operands_str:
                return None, None
            
            # Find all commas that are not inside parentheses
            paren_count = 0
            comma_indices = []
            
            for i, char in enumerate(operands_str):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == ',' and paren_count == 0:
                    comma_indices.append(i)
            
            if len(comma_indices) == 0:
                # Only one operand
                return operands_str.strip(), None
            elif len(comma_indices) == 1:
                # Two operands: split at the comma
                operand1_str = operands_str[:comma_indices[0]].strip()
                operand2_str = operands_str[comma_indices[0] + 1:].strip()
                return operand1_str, operand2_str
            else:
                # Three or more operands (e.g., imul $imm, src, dst)
                # Split into: operand1 = first part, operand2 = rest (src,dst)
                operand1_str = operands_str[:comma_indices[0]].strip()
                operand2_str = operands_str[comma_indices[0] + 1:].strip()
                return operand1_str, operand2_str
        
        operand1, operand2 = None, None
        if operands:
            op1_str, op2_str = split_operands(operands)
            operand1 = parse_operand(op1_str) if op1_str else None
            operand2 = parse_operand(op2_str) if op2_str else None
        instructions.append(Instruction(opcode, operand1, operand2))
    return instructions

class SymbolicExpr:
    """Symbolic expression for symbolic execution"""
    def __init__(self, expr_str):
        self.expr = expr_str
    
    def __str__(self):
        return self.expr
    
    def __repr__(self):
        return f"SymbolicExpr('{self.expr}')"
    
    def __add__(self, other):
        if isinstance(other, int):
            if other == 0:
                return self
            return SymbolicExpr(f"({self.expr} + {other})")
        return SymbolicExpr(f"({self.expr} + {other.expr})")
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if isinstance(other, int):
            if other == 0:
                return self
            return SymbolicExpr(f"({self.expr} - {other})")
        return SymbolicExpr(f"({self.expr} - {other.expr})")
    
    def __rsub__(self, other):
        if isinstance(other, int):
            return SymbolicExpr(f"({other} - {self.expr})")
        return SymbolicExpr(f"({other.expr} - {self.expr})")
    
    def __mul__(self, other):
        if isinstance(other, int):
            if other == 1:
                return self
            if other == 0:
                return 0
            return SymbolicExpr(f"({self.expr} * {other})")
        return SymbolicExpr(f"({self.expr} * {other.expr})")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __and__(self, other):
        if isinstance(other, int):
            return SymbolicExpr(f"({self.expr} & {other:#x})")
        return SymbolicExpr(f"({self.expr} & {other.expr})")
    
    def __or__(self, other):
        if isinstance(other, int):
            return SymbolicExpr(f"({self.expr} | {other:#x})")
        return SymbolicExpr(f"({self.expr} | {other.expr})")
    
    def __xor__(self, other):
        if isinstance(other, int):
            if other == 0:
                return self
            return SymbolicExpr(f"({self.expr} ^ {other:#x})")
        return SymbolicExpr(f"({self.expr} ^ {other.expr})")
    
    def __lshift__(self, other):
        if isinstance(other, int):
            if other == 0:
                return self
            return SymbolicExpr(f"({self.expr} << {other})")
        return SymbolicExpr(f"({self.expr} << {other.expr})")
    
    def __rlshift__(self, other):
        return self.__lshift__(other)

def symbolic_execute_search(instructions, line_number, V):
    """
    Perform symbolic execution forward and backward from line_number to find:
    1. Immediate values that directly use V
    2. Arithmetic/logical relationships involving V (e.g., output = input * V, output = input +/- V)
    
    Args:
        instructions: List of Instruction objects
        line_number: Starting line number (0-indexed)
        V: Target value to search for
    
    Returns:
        List of findings with type and description
    """
    if line_number < 0 or line_number >= len(instructions):
        return []
    
    findings = []
    n = len(instructions)
    
    # Initialize register state (using dict to track register values)
    # Values can be integers or SymbolicExpr objects
    registers = {}
    # Track which instruction last modified each register (for output instruction tracking)
    register_sources = {}  # reg_name -> (instruction_idx, direction)
    
    def get_operand_value(operand):
        """Get the value of an operand (register or immediate)"""
        if operand is None:
            return None
        if isinstance(operand, int):
            return operand
        if isinstance(operand, str) and operand.startswith('%'):
            # Register name
            reg_name = operand
            return registers.get(reg_name, SymbolicExpr(reg_name))
        return operand
    
    def set_register(reg_name, value, instr_idx=None, direction=None):
        """Set register value and track source instruction"""
        if isinstance(reg_name, str) and reg_name.startswith('%'):
            registers[reg_name] = value
            if instr_idx is not None:
                register_sources[reg_name] = (instr_idx, direction)
    
    def check_immediate_value(operand, instr_idx, direction):
        """Check if immediate value equals V"""
        if isinstance(operand, int) and operand == V:
            findings.append({
                'type': 'immediate_match',
                'line': instr_idx,
                'direction': direction,
                'instruction': instructions[instr_idx],
                'description': f"Found immediate value {V:#x} at line {instr_idx}"
            })
    
    def check_relationship(output_reg, input_reg, instr_idx, direction):
        """Check if there's a relationship between output and input involving V"""
        if output_reg not in registers:
            return
        
        output_expr = registers[output_reg]
        output_instr_idx = instr_idx
        input_instr_idx = None
        
        # Find input instruction (the instruction that last modified input_reg)
        if isinstance(input_reg, str) and input_reg.startswith('%'):
            if input_reg in register_sources:
                input_instr_idx, _ = register_sources[input_reg]
        
        # Check if output expression involves V
        if isinstance(output_expr, SymbolicExpr):
            expr_str = str(output_expr)
            input_reg_str = str(input_reg) if isinstance(input_reg, str) else str(input_reg)
            
            # Check for multiplication: (input * V) or (V * input)
            if f"({input_reg_str} * {V})" in expr_str or f"({V} * {input_reg_str})" in expr_str or \
               f"({input_reg_str} * {V:#x})" in expr_str or f"({V:#x} * {input_reg_str})" in expr_str:
                findings.append({
                    'type': 'multiplication',
                    'line': output_instr_idx,
                    'direction': direction,
                    'output_instruction': instructions[output_instr_idx],
                    'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                    'input_line': input_instr_idx,
                    'description': f"Found relationship: {output_reg} = {input_reg} * {V:#x}"
                })
            # Check for addition: (input + V)
            if f"({input_reg_str} + {V})" in expr_str or f"({input_reg_str} + {V:#x})" in expr_str:
                findings.append({
                    'type': 'addition',
                    'line': output_instr_idx,
                    'direction': direction,
                    'output_instruction': instructions[output_instr_idx],
                    'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                    'input_line': input_instr_idx,
                    'description': f"Found relationship: {output_reg} = {input_reg} + {V:#x}"
                })
            # Check for subtraction: (input - V) or (V - input)
            if f"({input_reg_str} - {V})" in expr_str or f"({input_reg_str} - {V:#x})" in expr_str:
                findings.append({
                    'type': 'subtraction',
                    'line': output_instr_idx,
                    'direction': direction,
                    'output_instruction': instructions[output_instr_idx],
                    'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                    'input_line': input_instr_idx,
                    'description': f"Found relationship: {output_reg} = {input_reg} - {V:#x}"
                })
            if f"({V} - {input_reg_str})" in expr_str or f"({V:#x} - {input_reg_str})" in expr_str:
                findings.append({
                    'type': 'subtraction_reverse',
                    'line': output_instr_idx,
                    'direction': direction,
                    'output_instruction': instructions[output_instr_idx],
                    'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                    'input_line': input_instr_idx,
                    'description': f"Found relationship: {output_reg} = {V:#x} - {input_reg}"
                })
        elif isinstance(output_expr, int):
            # If output is a concrete value, check if it equals V
            # But only if it's from an arithmetic/logical operation, not mov
            if output_expr == V:
                # Check if the instruction is mov - if so, don't create a relationship
                output_instr = instructions[output_instr_idx]
                if output_instr.opcode != 'mov':
                    findings.append({
                        'type': 'value_match',
                        'line': output_instr_idx,
                        'direction': direction,
                        'output_instruction': instructions[output_instr_idx],
                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                        'input_line': input_instr_idx,
                        'description': f"Found value match: {output_reg} = {V:#x}"
                    })
    
    def execute_instruction(instr, instr_idx, direction):
        """Execute a single instruction symbolically"""
        opcode = instr.opcode
        op1 = instr.operand1
        op2 = instr.operand2
        
        # Check immediate values
        check_immediate_value(op1, instr_idx, direction)
        check_immediate_value(op2, instr_idx, direction)
        
        # Execute instruction (AT&T syntax: op src, dst means dst = dst op src)
        if opcode == 'add':
            if isinstance(op2, str) and op2.startswith('%'):
                # add $imm, %reg or add %reg1, %reg2
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    # add $imm, %reg: %reg = %reg + imm
                    # Get input instruction before updating register
                    input_instr_idx = None
                    if op1 == V and op2 in register_sources:
                        prev_instr_idx, _ = register_sources[op2]
                        if prev_instr_idx is not None and prev_instr_idx != instr_idx:
                            input_instr_idx = prev_instr_idx
                    
                    new_val = dst_val + op1
                    set_register(op2, new_val, instr_idx, direction)
                    # Check relationship: output = input + V
                    if op1 == V:
                        # Direct relationship: output = input + V
                        findings.append({
                            'type': 'addition',
                            'line': instr_idx,
                            'direction': direction,
                            'output_instruction': instructions[instr_idx],
                            'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                            'input_line': input_instr_idx,
                            'description': f"Found relationship: {op2} = {op2} + {V:#x}"
                        })
                    if isinstance(dst_val, SymbolicExpr):
                        check_relationship(op2, op2, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    # add %reg1, %reg2: %reg2 = %reg2 + %reg1
                    src_val = get_operand_value(op1)
                    new_val = dst_val + src_val
                    set_register(op2, new_val, instr_idx, direction)
                    check_relationship(op2, op1, instr_idx, direction)
        elif opcode == 'sub':
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    # sub $imm, %reg: %reg = %reg - imm
                    # Get input instruction before updating register
                    input_instr_idx = None
                    if op1 == V and op2 in register_sources:
                        prev_instr_idx, _ = register_sources[op2]
                        if prev_instr_idx is not None and prev_instr_idx != instr_idx:
                            input_instr_idx = prev_instr_idx
                    
                    new_val = dst_val - op1
                    set_register(op2, new_val, instr_idx, direction)
                    # Check relationship: output = input - V
                    if op1 == V:
                        findings.append({
                            'type': 'subtraction',
                            'line': instr_idx,
                            'direction': direction,
                            'output_instruction': instructions[instr_idx],
                            'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                            'input_line': input_instr_idx,
                            'description': f"Found relationship: {op2} = {op2} - {V:#x}"
                        })
                    if isinstance(dst_val, SymbolicExpr):
                        check_relationship(op2, op2, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    # sub %reg1, %reg2: %reg2 = %reg2 - %reg1
                    src_val = get_operand_value(op1)
                    new_val = dst_val - src_val
                    set_register(op2, new_val, instr_idx, direction)
                    check_relationship(op2, op1, instr_idx, direction)
        elif opcode == 'and':
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    # and $imm, %reg: %reg = %reg & imm
                    new_val = dst_val & op1
                    set_register(op2, new_val, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    # and %reg1, %reg2: %reg2 = %reg2 & %reg1
                    src_val = get_operand_value(op1)
                    new_val = dst_val & src_val
                    set_register(op2, new_val, instr_idx, direction)
        elif opcode == 'or':
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    # or $imm, %reg: %reg = %reg | imm
                    new_val = dst_val | op1
                    set_register(op2, new_val, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    # or %reg1, %reg2: %reg2 = %reg2 | %reg1
                    src_val = get_operand_value(op1)
                    new_val = dst_val | src_val
                    set_register(op2, new_val, instr_idx, direction)
        elif opcode == 'xor':
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    # xor $imm, %reg: %reg = %reg ^ imm
                    new_val = dst_val ^ op1
                    set_register(op2, new_val, instr_idx, direction)
                    # Check if result is 0 (when V=0)
                    if V == 0 and isinstance(new_val, int) and new_val == 0:
                        findings.append({
                            'type': 'zero_assignment',
                            'line': instr_idx,
                            'direction': direction,
                            'output_instruction': instructions[instr_idx],
                            'input_instruction': None,
                            'input_line': None,
                            'description': f"Found relationship: {op2} = 0 (via xor with immediate)"
                        })
                elif isinstance(op1, str) and op1.startswith('%'):
                    # xor %reg1, %reg2: %reg2 = %reg2 ^ %reg1
                    # Special case: xor %reg, %reg sets register to 0 (common optimization)
                    if op1 == op2:
                        # xor %reg, %reg = 0
                        set_register(op2, 0, instr_idx, direction)
                        # Check if V=0
                        if V == 0:
                            findings.append({
                                'type': 'zero_assignment',
                                'line': instr_idx,
                                'direction': direction,
                                'output_instruction': instructions[instr_idx],
                                'input_instruction': None,
                                'input_line': None,
                                'description': f"Found relationship: {op2} = 0 (via xor {op2}, {op2})"
                            })
                    else:
                        src_val = get_operand_value(op1)
                        new_val = dst_val ^ src_val
                        set_register(op2, new_val, instr_idx, direction)
                        # Check relationship
                        check_relationship(op2, op1, instr_idx, direction)
        elif opcode == 'sbb':
            # sbb %reg1, %reg2: reg2 = reg2 - reg1 - CF
            # Simplified: reg2 = reg2 - reg1 (ignoring CF for now)
            if isinstance(op1, str) and op1.startswith('%') and isinstance(op2, str) and op2.startswith('%'):
                val1 = get_operand_value(op1)
                val2 = get_operand_value(op2)
                new_val = val2 - val1
                set_register(op2, new_val, instr_idx, direction)
                check_relationship(op2, op1, instr_idx, direction)
        elif opcode == 'mov':
            if isinstance(op2, str) and op2.startswith('%'):
                # mov $imm, %reg or mov %reg1, %reg2
                # Note: mov is data movement, not arithmetic/logical operation
                # So we don't check relationships for mov instructions
                if isinstance(op1, int):
                    set_register(op2, op1, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    val = get_operand_value(op1)
                    set_register(op2, val, instr_idx, direction)
                    # Don't check relationship for mov - it's just data copying
        elif opcode == 'movslq' or opcode == 'movsx' or opcode == 'movs':
            # movslq src, dst: sign-extend and move (same as mov for our purposes)
            if isinstance(op2, str) and op2.startswith('%'):
                if isinstance(op1, str) and op1.startswith('%'):
                    val = get_operand_value(op1)
                    set_register(op2, val, instr_idx, direction)
        elif opcode == 'shl' or opcode == 'sal':
            # shl $imm, %reg: %reg = %reg << imm
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    new_val = dst_val << op1
                    set_register(op2, new_val, instr_idx, direction)
                    # Check if this creates a multiplication relationship
                    if isinstance(dst_val, SymbolicExpr):
                        check_relationship(op2, op2, instr_idx, direction)
        elif opcode == 'shr' or opcode == 'sar':
            # shr $imm, %reg: %reg = %reg >> imm
            # sar $imm, %reg: %reg = %reg >> imm (arithmetic right shift, same as logical for our purposes)
            if isinstance(op2, str) and op2.startswith('%'):
                dst_val = get_operand_value(op2)
                if isinstance(op1, int):
                    new_val = SymbolicExpr(f"({dst_val.expr} >> {op1})")
                    set_register(op2, new_val, instr_idx, direction)
                    # Check if this creates a division relationship
                    # If dst_val is a simple register and op1 corresponds to V (2^op1 = V)
                    if isinstance(dst_val, SymbolicExpr) and str(dst_val) == op2:
                        # dst_val is the input register itself
                        # Check if 2^op1 == V
                        import math
                        if V > 0 and (V & (V - 1)) == 0:  # V is power of 2
                            shift = int(math.log2(V))
                            if op1 == shift:
                                findings.append({
                                    'type': 'division',
                                    'line': instr_idx,
                                    'direction': direction,
                                    'output_instruction': instructions[instr_idx],
                                    'input_instruction': None,
                                    'input_line': None,
                                    'description': f"Found relationship: {op2} = {op2} / {V:#x} (via {opcode} $0x{op1:x}, {op2})"
                                })
        elif opcode == 'lea':
            # lea src, dst: dst = address of src
            # lea is often used for fast arithmetic: lea (%rdx,%rdx,4),%rcx means rcx = rdx*5
            if isinstance(op2, str) and op2.startswith('%'):
                # Parse address expression like (%rdx,%rdx,4) or (%rdx,%rax,1) or -0x8(%rbp)
                if isinstance(op1, str):
                    # Try to parse address expression
                    addr_expr = op1.strip()
                    # Pattern: (base,index,scale) or (base) or offset(base) or offset(base,index,scale)
                    # For now, handle common patterns
                    lea_result = parse_lea_expression(addr_expr, registers, get_operand_value)
                    if lea_result is not None:
                        set_register(op2, lea_result, instr_idx, direction)
                        # Check if this creates a relationship with V
                        if isinstance(lea_result, SymbolicExpr):
                            # Try to find input register in the expression
                            for reg_name in registers:
                                if reg_name in str(lea_result):
                                    check_relationship(op2, reg_name, instr_idx, direction)
        elif opcode == 'imul':
            # imul $imm, src, dst: dst = src * imm
            # or imul src, dst: dst = dst * src
            # Note: For imul with immediate, the immediate is sign-extended to match operand size
            if isinstance(op2, str) and op2.startswith('%'):
                if isinstance(op1, int):
                    # imul $imm, src, dst format
                    # op2 might be "src,dst" or just "dst"
                    # For large immediate values that look like they should be negative,
                    # we should interpret them as signed. But in the expression, we'll keep
                    # the value as-is and let the evaluation handle it.
                    if ',' in op2:
                        # Three-operand format: imul $imm, src, dst
                        parts = op2.split(',')
                        if len(parts) >= 2:
                            src_reg = parts[0].strip()
                            dst_reg = parts[1].strip()
                            src_val = get_operand_value(src_reg)
                            # For expression generation, use the value as-is
                            # The sign interpretation will be handled during evaluation if needed
                            new_val = src_val * op1
                            set_register(dst_reg, new_val, instr_idx, direction)
                            # Check relationship
                            if isinstance(src_val, SymbolicExpr):
                                check_relationship(dst_reg, src_reg, instr_idx, direction)
                    else:
                        # Two-operand format: imul $imm, dst means dst = dst * imm
                        dst_val = get_operand_value(op2)
                        new_val = dst_val * op1
                        set_register(op2, new_val, instr_idx, direction)
                        if isinstance(dst_val, SymbolicExpr):
                            check_relationship(op2, op2, instr_idx, direction)
                elif isinstance(op1, str) and op1.startswith('%'):
                    # imul src, dst: dst = dst * src
                    if ',' in op2:
                        # Three-operand format might have src,dst in op2
                        parts = op2.split(',')
                        if len(parts) >= 2:
                            src_reg = parts[0].strip()
                            dst_reg = parts[1].strip()
                            src_val = get_operand_value(src_reg)
                            dst_val = get_operand_value(dst_reg)
                            new_val = dst_val * src_val
                            set_register(dst_reg, new_val, instr_idx, direction)
                            check_relationship(dst_reg, src_reg, instr_idx, direction)
                    else:
                        # Two-operand format: imul src, dst means dst = dst * src
                        src_val = get_operand_value(op1)
                        dst_val = get_operand_value(op2)
                        new_val = dst_val * src_val
                        set_register(op2, new_val, instr_idx, direction)
                        check_relationship(op2, op1, instr_idx, direction)
        elif opcode == 'cmp':
            # cmp doesn't modify registers, but we already checked immediate values above
            pass
    
    def parse_lea_expression(addr_expr, registers, get_operand_value):
        """
        Parse LEA address expression and compute the symbolic result.
        Examples:
        - (%rdx,%rdx,4) -> rdx + rdx*4 = rdx*5
        - (%rdx) -> rdx
        - -0x8(%rbp) -> rbp - 8
        - 0xb90(%rsi,%rax,1) -> rsi + rax*1 + 0xb90
        """
        import re
        
        # Remove whitespace
        addr_expr = addr_expr.strip()
        
        # Pattern 1: (base,index,scale) or (base,index) or (base)
        # Match: (%rdx,%rdx,4) or (%rdx,%rax) or (%rdx)
        match = re.match(r'\(([^,)]+)(?:,([^,)]+)(?:,([^)]+))?)?\)', addr_expr)
        if match:
            base = match.group(1).strip()
            index = match.group(2).strip() if match.group(2) else None
            scale = match.group(3).strip() if match.group(3) else None
            
            result = None
            
            # Get base value
            if base.startswith('%'):
                base_val = get_operand_value(base)
            else:
                # Base is an offset (shouldn't happen in this pattern, but handle it)
                try:
                    if base.startswith('0x'):
                        base_val = int(base, 16)
                    else:
                        base_val = int(base, 10)
                except:
                    return None
            
            result = base_val
            
            # Add index*scale if present
            if index and index.startswith('%'):
                index_val = get_operand_value(index)
                if scale:
                    try:
                        if scale.startswith('0x'):
                            scale_val = int(scale, 16)
                        else:
                            scale_val = int(scale, 10)
                    except:
                        scale_val = 1
                else:
                    scale_val = 1
                
                if result is None:
                    result = index_val * scale_val
                else:
                    result = result + (index_val * scale_val)
            
            return result
        
        # Pattern 2: offset(base) or offset(base,index,scale) or offset(,index,scale)
        # Match: -0x8(%rbp) or 0xb90(%rsi,%rax,1) or 0x0(,%rax,4)
        # Allow empty base (comma at start)
        match = re.match(r'([+-]?[0-9a-fx]+)?\(([^,)]*)(?:,([^,)]+)(?:,([^)]+))?)?\)', addr_expr)
        if match:
            offset_str = match.group(1) if match.group(1) else None
            base = match.group(2).strip() if match.group(2) else None
            index = match.group(3).strip() if match.group(3) else None
            scale = match.group(4).strip() if match.group(4) else None
            
            result = None
            
            # Parse offset
            if offset_str:
                try:
                    if offset_str.startswith('0x') or offset_str.startswith('-0x') or offset_str.startswith('+0x'):
                        offset_val = int(offset_str, 16)
                    else:
                        offset_val = int(offset_str, 10)
                    result = offset_val
                except:
                    pass
            
            # Get base value (if present)
            if base and base.startswith('%'):
                base_val = get_operand_value(base)
                if result is None:
                    result = base_val
                else:
                    result = result + base_val
            
            # Add index*scale if present
            if index and index.startswith('%'):
                index_val = get_operand_value(index)
                if scale:
                    try:
                        if scale.startswith('0x'):
                            scale_val = int(scale, 16)
                        else:
                            scale_val = int(scale, 10)
                    except:
                        scale_val = 1
                else:
                    scale_val = 1
                
                if result is None:
                    result = index_val * scale_val
                else:
                    result = result + (index_val * scale_val)
            
            return result
        
        # Pattern 3: Just a register (shouldn't happen with LEA, but handle it)
        if addr_expr.startswith('%'):
            return get_operand_value(addr_expr)
        
        return None
    
    def check_final_relationships():
        """Check final register values for multiplication relationships with V"""
        # Find the initial input register (the first register that gets a value from memory or is set)
        initial_regs = set()
        for i in range(n):
            instr = instructions[i]
            if instr.opcode == 'mov' and isinstance(instr.operand2, str) and instr.operand2.startswith('%'):
                # Check if operand1 is from memory (like -0x8(%rbp))
                if isinstance(instr.operand1, str) and '(' in instr.operand1:
                    initial_regs.add(instr.operand2)
                # Or if it's a register-to-register move from an initial register
                elif isinstance(instr.operand1, str) and instr.operand1.startswith('%'):
                    if instr.operand1 in initial_regs:
                        initial_regs.add(instr.operand2)
            # Also check lea instructions - registers used in lea address expressions might be initial
            elif instr.opcode == 'lea' and isinstance(instr.operand1, str):
                # Extract registers from lea address expression
                import re
                addr_expr = instr.operand1
                # Find all register names in the expression
                reg_matches = re.findall(r'%[a-z0-9]+', addr_expr)
                for reg_name in reg_matches:
                    # If this register is not in registers dict or is a simple SymbolicExpr, it's likely an initial input
                    if reg_name not in registers:
                        initial_regs.add(reg_name)
                    elif isinstance(registers.get(reg_name, None), SymbolicExpr):
                        # Check if it's a simple register name (not a complex expression)
                        reg_val = registers[reg_name]
                        if str(reg_val) == reg_name:
                            initial_regs.add(reg_name)
            # Check for registers used as source operands in other instructions
            # If a register is used but has a simple SymbolicExpr value, it's likely an initial input
            elif instr.opcode in ['add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'sar', 'sbb']:
                # Check operand1 (source)
                if isinstance(instr.operand1, str) and instr.operand1.startswith('%'):
                    reg_name = instr.operand1
                    if reg_name not in registers:
                        initial_regs.add(reg_name)
                    elif isinstance(registers.get(reg_name, None), SymbolicExpr):
                        reg_val = registers[reg_name]
                        if str(reg_val) == reg_name:
                            initial_regs.add(reg_name)
        
        # Check all registers for multiplication relationships
        # Also check registers that might have been modified but are not in registers dict
        # (e.g., final values stored to memory)
        all_regs_to_check = list(registers.keys())
        # Sort registers by the instruction index that last modified them
        # This ensures we check the final result registers first (they're modified later)
        regs_with_indices = []
        for reg_name in all_regs_to_check:
            if reg_name in register_sources:
                instr_idx, _ = register_sources[reg_name]
                regs_with_indices.append((reg_name, instr_idx))
            else:
                # If not in register_sources, assume it was modified early (check later)
                regs_with_indices.append((reg_name, -1))
        # Sort by instruction index (descending) - latest modifications first
        regs_with_indices.sort(key=lambda x: x[1], reverse=True)
        
        # Check registers in order (latest first)
        # Track if we've already found a relationship to avoid duplicates
        found_relationships = set()
        # For magic number divisions, collect ALL matching registers first,
        # then report only the one modified latest (final result)
        magic_div_candidates = []  # [(reg_name, instr_idx, initial_reg, expr_str)]
        
        for reg_name, _ in regs_with_indices:
            if reg_name not in registers:
                continue
            reg_value = registers[reg_name]
            if isinstance(reg_value, SymbolicExpr):
                expr_str = str(reg_value)
                # Check if expression can be simplified to input * V
                # Look for patterns like: (input * V), (V * input), or complex expressions that equal input * V
                for initial_reg in initial_regs:
                    initial_reg_str = str(initial_reg)
                    # Skip if the register name doesn't appear in the expression
                    if initial_reg_str not in expr_str:
                        continue
                    
                    # Create a unique key for this relationship to avoid duplicates
                    relationship_key = (reg_name, initial_reg_str, V)
                    if relationship_key in found_relationships:
                        continue
                    
                    # For complex expressions, try a pattern-based approach for division detection
                    # If the expression contains imul with a large constant followed by shifts,
                    # it might be a magic number division
                    # Check if the expression structure suggests division by V
                    # Check if instructions contain imul (case-insensitive)
                    has_imul_instr = any('imul' in str(instr).lower() for instr in instructions)
                    if has_imul_instr or len(expr_str) > 50:
                        # Try to detect magic number division pattern
                        # Pattern: imul with large constant, then shifts and adds
                        # This is a heuristic - if we see this pattern and V is in a reasonable range,
                        # try to verify division relationship with a more lenient test
                        magic_number_pattern = r'\* (\d{8,})'  # Large constant (8+ digits, like magic numbers)
                        import re
                        # Also check for hex patterns in the expression (magic numbers are often large)
                        has_large_constant = re.search(magic_number_pattern, expr_str)
                        # Check if expression has imul-like pattern (multiplication with large number)
                        has_imul_pattern = '>>' in expr_str and '*' in expr_str
                        # For magic number divisions, the expression typically has:
                        # - Large constant multiplication
                        # - Right shifts
                        # - Addition/subtraction
                        # Also check if the expression contains a subtraction that might be sign correction
                        # (e.g., (complex_expr) - (something >> 31))
                        has_subtraction_pattern = '-' in expr_str and '>>' in expr_str
                        # Check if expression references other registers that might contain magic number
                        # For example, if %eax = %edx - %ecx, and %edx contains magic number, we should detect it
                        # Note: Need to handle 32-bit/64-bit register name mapping (e.g., %rdx <-> %edx)
                        references_other_regs = False
                        for other_reg in registers:
                            # Check if other_reg or its 32/64-bit variant appears in expr_str
                            # Map between 64-bit and 32-bit register names
                            reg_variants = [other_reg]
                            if other_reg.startswith('%r') and other_reg.endswith('x'):
                                # 64-bit -> 32-bit: %rax -> %eax, %rdx -> %edx, etc.
                                reg_variants.append('%e' + other_reg[2:])
                            elif other_reg.startswith('%e') and other_reg.endswith('x'):
                                # 32-bit -> 64-bit: %eax -> %rax, %edx -> %rdx, etc.
                                reg_variants.append('%r' + other_reg[2:])
                            
                            # Check if any variant appears in expr_str
                            found_in_expr = any(variant != reg_name and variant in expr_str for variant in reg_variants)
                            if found_in_expr:
                                # Check if this register or its 32/64-bit variant contains magic number
                                # For example, if expr_str contains %edx, check both %edx and %rdx
                                for check_reg in [other_reg] + reg_variants:
                                    if check_reg in registers:
                                        other_expr = str(registers.get(check_reg, ''))
                                        if other_expr and isinstance(registers.get(check_reg), SymbolicExpr):
                                            # Check if the other register's expression contains magic number
                                            if re.search(magic_number_pattern, other_expr):
                                                # This register's expression references another register that has magic number
                                                references_other_regs = True
                                                break
                                if references_other_regs:
                                    break
                                    # Also check recursively - if other_reg references yet another reg with magic number
                                    for yet_another_reg in registers:
                                        yet_another_variants = [yet_another_reg]
                                        if yet_another_reg.startswith('%r') and yet_another_reg.endswith('x'):
                                            yet_another_variants.append('%e' + yet_another_reg[2:])
                                        elif yet_another_reg.startswith('%e') and yet_another_reg.endswith('x'):
                                            yet_another_variants.append('%r' + yet_another_reg[2:])
                                        
                                        if any(variant != reg_name and variant != other_reg and variant in other_expr 
                                              for variant in yet_another_variants):
                                            yet_another_expr = str(registers.get(yet_another_reg, ''))
                                            if yet_another_expr and isinstance(registers.get(yet_another_reg), SymbolicExpr):
                                                if re.search(magic_number_pattern, yet_another_expr):
                                                    references_other_regs = True
                                                    break
                                    if references_other_regs:
                                        break
                        
                        if has_large_constant or (has_imul_pattern and len(expr_str) > 50) or \
                           (has_subtraction_pattern and has_imul_pattern) or \
                           (references_other_regs and has_imul_instr):
                            # Likely a magic number division - use pattern-based detection
                            # For magic number divisions, the expression structure is very specific:
                            # imul with large constant, shifts, and arithmetic operations
                            # If we see this pattern and V is reasonable, it's likely a division by V
                            
                            # Try to verify with test values, but use very lenient criteria
                            test_pattern_values = [V, V * 2, V * 3] if V > 0 and V < 1000 else [V, V * 2]
                            pattern_match_count = 0
                            verified_division = False
                            
                            for pattern_test in test_pattern_values:
                                if pattern_test <= 0 or pattern_test > 10000:  # Skip unreasonable values
                                    continue
                                try:
                                    pattern_expr = expr_str.replace(initial_reg_str, str(pattern_test))
                                    pattern_expr = re.sub(r'\(' + re.escape(initial_reg_str) + r'\)', f'({pattern_test})', pattern_expr)
                                    pattern_expr = re.sub(r'\(' + re.escape(initial_reg_str) + r'\b', f'({pattern_test}', pattern_expr)
                                    pattern_expr = re.sub(r'\b' + re.escape(initial_reg_str) + r'\)', f'{pattern_test})', pattern_expr)
                                    pattern_expr = re.sub(r'\b' + re.escape(initial_reg_str) + r'\b', str(pattern_test), pattern_expr)
                                    pattern_result = eval(pattern_expr)
                                    
                                    # Try multiple interpretations of the result
                                    test_results = [pattern_result]
                                    # Try 32-bit masking
                                    if pattern_result > (1 << 32):
                                        test_results.append(pattern_result & 0xffffffff)
                                    # Try signed 32-bit
                                    if pattern_result > (1 << 31):
                                        test_results.append((pattern_result & 0xffffffff) - (1 << 32))
                                    
                                    for test_result in test_results:
                                        if test_result == 0:
                                            continue
                                        # Check if result * V is approximately equal to test_input
                                        # Use very large tolerance for magic number divisions
                                        calculated = test_result * V
                                        # For magic number divisions, the result might be approximate
                                        # Use tolerance based on V and test_input
                                        pattern_tolerance = max(V * 20, abs(pattern_test) * 2)  # Very large tolerance
                                        if abs(calculated - pattern_test) <= pattern_tolerance:
                                            pattern_match_count += 1
                                            verified_division = True
                                            break
                                    if verified_division:
                                        break
                                except:
                                    pass
                            
                            # If we have the magic number pattern and V is reasonable, report as division
                            # The pattern of imul with large constant + shifts is very specific to division
                            # Even if exact verification fails due to expression evaluation issues,
                            # the pattern itself is strong evidence
                            if has_large_constant and V > 0 and V < 10000:  # V is reasonable
                                # Strong pattern match - report as division
                                pattern_match_count = 1  # Treat as verified
                            elif references_other_regs and has_imul_instr and V > 0 and V < 10000:
                                # Also treat as verified if we reference another register with magic number
                                pattern_match_count = 1
                            
                            # For magic number divisions, we want to find the FINAL instruction
                            # that completes the computation. Check all registers with the pattern
                            # and find the one modified latest (the final result)
                            this_reg_instr_idx = register_sources.get(reg_name, (-1, 'forward'))[0]
                            
                            # Find the latest instruction index among all registers with the magic number pattern
                            latest_instr_idx = this_reg_instr_idx
                            latest_reg_name = reg_name
                            for other_reg_name in registers:
                                if other_reg_name in register_sources:
                                    other_instr_idx = register_sources[other_reg_name][0]
                                    if other_instr_idx > latest_instr_idx:
                                        # Check if other_reg also has the magic number pattern
                                        other_expr = str(registers.get(other_reg_name, ''))
                                        if isinstance(registers.get(other_reg_name), SymbolicExpr) and \
                                           initial_reg_str in other_expr:
                                            # Check if it has the pattern (directly or via references)
                                            other_has_large_constant = re.search(magic_number_pattern, other_expr)
                                            other_references_magic = False
                                            for ref_reg in registers:
                                                if ref_reg != other_reg_name and ref_reg in other_expr:
                                                    ref_expr = str(registers.get(ref_reg, ''))
                                                    if isinstance(registers.get(ref_reg), SymbolicExpr) and \
                                                       re.search(magic_number_pattern, ref_expr):
                                                        other_references_magic = True
                                                        break
                                            
                                            if other_has_large_constant or (other_references_magic and has_imul_instr):
                                                latest_instr_idx = other_instr_idx
                                                latest_reg_name = other_reg_name
                            
                            # Collect this as a candidate for magic number division
                            if pattern_match_count >= 1:
                                instr_idx = register_sources.get(reg_name, (-1, 'forward'))[0]
                                magic_div_candidates.append((reg_name, instr_idx, initial_reg, expr_str))
                                # Continue to check other registers
                                continue
                            
                            # OLD CODE (commented out - we'll process candidates later)
                            # Only report if this is the latest register with the pattern
                            if False and pattern_match_count >= 1 and reg_name == latest_reg_name:
                                # Find the instruction that last modified this register
                                # For magic number divisions, we want to find the final instruction
                                # that completes the division, not an intermediate step
                                output_instr_idx = None
                                direction = 'forward'
                                
                                # Find the last instruction that modifies this register
                                # This is important for magic number divisions where the result
                                # might be moved between registers and then corrected
                                # We want the FINAL instruction that completes the computation
                                # For magic number divisions, we want the LAST arithmetic/logical operation,
                                # not an intermediate step like a mov
                                
                                # First, find ALL instructions that modify this register
                                modifying_instrs = []
                                for i in range(n):
                                    instr = instructions[i]
                                    if isinstance(instr.operand2, str) and instr.operand2 == reg_name:
                                        modifying_instrs.append((i, instr))
                                
                                # Among all modifying instructions, find the last arithmetic/logical operation
                                # (prefer arithmetic over mov)
                                last_arithmetic_instr_idx = None
                                last_mov_instr_idx = None
                                for i, instr in modifying_instrs:
                                    if instr.opcode in ['add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'sar', 'imul']:
                                        last_arithmetic_instr_idx = i
                                    elif instr.opcode == 'mov':
                                        last_mov_instr_idx = i
                                
                                # Use the last arithmetic operation if available, otherwise use the last mov
                                if last_arithmetic_instr_idx is not None:
                                    output_instr_idx = last_arithmetic_instr_idx
                                elif last_mov_instr_idx is not None:
                                    # If the last instruction is mov, check if there's a later arithmetic operation
                                    # that further modifies the register (for sign correction, etc.)
                                    output_instr_idx = last_mov_instr_idx
                                    for i in range(last_mov_instr_idx + 1, n):
                                        instr = instructions[i]
                                        if isinstance(instr.operand2, str) and instr.operand2 == reg_name and \
                                           instr.opcode in ['add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'sar']:
                                            # Found a later arithmetic operation - use that instead
                                            output_instr_idx = i
                                            break
                                
                                # If we found an instruction via register_sources, use it as fallback
                                if output_instr_idx is None and reg_name in register_sources:
                                    output_instr_idx, direction = register_sources[reg_name]
                                elif output_instr_idx is not None and reg_name in register_sources:
                                    # Update direction from register_sources
                                    _, direction = register_sources[reg_name]
                                
                                if output_instr_idx is not None:
                                    output_instr = instructions[output_instr_idx]
                                    # For magic number divisions, even if the last instruction is mov,
                                    # we still want to report the relationship
                                    input_instr_idx = None
                                    for i in range(n):
                                        if instructions[i].opcode == 'mov' and \
                                           isinstance(instructions[i].operand2, str) and \
                                           instructions[i].operand2 == initial_reg:
                                            input_instr_idx = i
                                            break
                                    
                                    findings.append({
                                        'type': 'division',
                                        'line': output_instr_idx,
                                        'direction': direction,
                                        'output_instruction': instructions[output_instr_idx],
                                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                        'input_line': input_instr_idx,
                                        'description': f"Found relationship: {reg_name} = {initial_reg} / {V:#x} (magic number division)"
                                    })
                                    found_relationships.add(relationship_key)
                                    continue  # Skip the normal division detection below
                    # Try to find multiplication patterns
                    # Check for direct multiplication: (input * V) or (V * input)
                    if f"({initial_reg_str} * {V})" in expr_str or f"({V} * {initial_reg_str})" in expr_str or \
                       f"({initial_reg_str} * {V:#x})" in expr_str or f"({V:#x} * {initial_reg_str})" in expr_str:
                        # Find the instruction that last modified this register
                        if reg_name in register_sources:
                            output_instr_idx, direction = register_sources[reg_name]
                            output_instr = instructions[output_instr_idx]
                            # Don't create relationship for mov instructions
                            if output_instr.opcode != 'mov':
                                # Find the input instruction (first instruction that set initial_reg)
                                input_instr_idx = None
                                for i in range(n):
                                    if instructions[i].opcode == 'mov' and \
                                       isinstance(instructions[i].operand2, str) and \
                                       instructions[i].operand2 == initial_reg:
                                        input_instr_idx = i
                                        break
                                # If not found, try to find lea instruction that uses initial_reg
                                # But don't use the same instruction as output
                                if input_instr_idx is None:
                                    for i in range(n):
                                        if i != output_instr_idx and \
                                           instructions[i].opcode == 'lea' and \
                                           isinstance(instructions[i].operand1, str) and \
                                           initial_reg in instructions[i].operand1:
                                            input_instr_idx = i
                                            break
                                
                                findings.append({
                                    'type': 'multiplication',
                                    'line': output_instr_idx,
                                    'direction': direction,
                                    'output_instruction': instructions[output_instr_idx],
                                    'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                    'input_line': input_instr_idx,
                                    'description': f"Found relationship: {reg_name} = {initial_reg} * {V:#x}"
                                })
                    # Check for division relationship: if output = input >> shift, then input = output * (2^shift)
                    # Pattern: (input >> shift) where 2^shift = V
                    import math
                    # Check if V is a power of 2
                    if V > 0 and (V & (V - 1)) == 0:  # V is power of 2
                        shift = int(math.log2(V))
                        # Check for pattern: (input >> shift)
                        if f"({initial_reg_str} >> {shift})" in expr_str:
                            # Find the instruction that last modified this register
                            if reg_name in register_sources:
                                output_instr_idx, direction = register_sources[reg_name]
                                output_instr = instructions[output_instr_idx]
                                # Don't create relationship for mov instructions
                                if output_instr.opcode != 'mov':
                                    # Find the input instruction
                                    input_instr_idx = None
                                    for i in range(n):
                                        if instructions[i].opcode == 'mov' and \
                                           isinstance(instructions[i].operand2, str) and \
                                           instructions[i].operand2 == initial_reg:
                                            input_instr_idx = i
                                            break
                                    # If not found, try to find lea instruction that uses initial_reg
                                    if input_instr_idx is None:
                                        for i in range(n):
                                            if i != output_instr_idx and \
                                               instructions[i].opcode == 'lea' and \
                                               isinstance(instructions[i].operand1, str) and \
                                               initial_reg in instructions[i].operand1:
                                                input_instr_idx = i
                                                break
                                    
                                    findings.append({
                                        'type': 'division',
                                        'line': output_instr_idx,
                                        'direction': direction,
                                        'output_instruction': instructions[output_instr_idx],
                                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                        'input_line': input_instr_idx,
                                        'description': f"Found relationship: {reg_name} = {initial_reg} / {V:#x} (implies {initial_reg} = {reg_name} * {V:#x})"
                                    })
                    
                    # Check for modulo relationship: if output = input - (input/V) * V, then output = input % V
                    # Pattern: (input - (something * V)) where something might be (input / V)
                    # We can check if the expression evaluates to input % V
                    try:
                        # Try evaluating with multiple test values to verify modulo relationship
                        # For modulo V: input % V should equal (input % V) for any input
                        test_values = [V, V + 1, 2 * V, 2 * V + 1, V - 1 if V > 1 else 1]
                        modulo_match = True
                        for test_input in test_values:
                            test_expr = expr_str.replace(initial_reg_str, str(test_input))
                            # Handle register name in parentheses
                            test_expr = test_expr.replace(f"({initial_reg_str}", f"({test_input}")
                            test_expr = test_expr.replace(f"{initial_reg_str})", f"{test_input})")
                            try:
                                eval_result = eval(test_expr)
                                expected = test_input % V
                                if eval_result != expected:
                                    modulo_match = False
                                    break
                            except:
                                modulo_match = False
                                break
                        
                        if modulo_match:
                            # Likely modulo relationship
                            if reg_name in register_sources:
                                output_instr_idx, direction = register_sources[reg_name]
                                output_instr = instructions[output_instr_idx]
                                if output_instr.opcode != 'mov':
                                    input_instr_idx = None
                                    for i in range(n):
                                        if instructions[i].opcode == 'mov' and \
                                           isinstance(instructions[i].operand2, str) and \
                                           instructions[i].operand2 == initial_reg:
                                            input_instr_idx = i
                                            break
                                    
                                    findings.append({
                                        'type': 'modulo',
                                        'line': output_instr_idx,
                                        'direction': direction,
                                        'output_instruction': instructions[output_instr_idx],
                                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                        'input_line': input_instr_idx,
                                        'description': f"Found relationship: {reg_name} = {initial_reg} % {V:#x}"
                                    })
                    except Exception as e:
                        # Silently ignore evaluation errors
                        pass
                    
                    # Check for division relationship: if output * V = input, then output = input / V
                    # This handles complex division operations using magic numbers
                    # We check if the expression evaluates to input / V for multiple test values
                    try:
                        # Try evaluating with multiple test values
                        # For division by V: output(input) should equal input / V
                        test_values = [V, 2 * V, 3 * V if V > 0 and V < 1000 else V + 1]
                        division_match = True
                        match_count = 0
                        for test_input in test_values:
                            if test_input <= 0:
                                continue
                            # More robust replacement: use regex to replace all occurrences
                            import re
                            # Replace the register name, handling various contexts
                            # First replace in parentheses
                            test_expr = re.sub(r'\(' + re.escape(initial_reg_str) + r'\)', f'({test_input})', expr_str)
                            test_expr = re.sub(r'\(' + re.escape(initial_reg_str) + r'\b', f'({test_input}', test_expr)
                            test_expr = re.sub(r'\b' + re.escape(initial_reg_str) + r'\)', f'{test_input})', test_expr)
                            # Then replace standalone occurrences (word boundary)
                            test_expr = re.sub(r'\b' + re.escape(initial_reg_str) + r'\b', str(test_input), test_expr)
                            
                            # Handle arithmetic right shift for signed numbers
                            # Python's >> does arithmetic shift for negative numbers, but we need to ensure
                            # large numbers are handled correctly
                            # Replace >> with a function that handles signed arithmetic shift
                            def arith_rshift(a, b):
                                """Arithmetic right shift that handles large numbers correctly"""
                                if a < 0:
                                    # For negative numbers, Python's >> already does arithmetic shift
                                    return a >> b
                                else:
                                    # For positive numbers, check if result should be negative
                                    # This is a simplified version - in reality, we'd need to know the bit width
                                    result = a >> b
                                    # If the high bit was set before shift, preserve sign
                                    # For 64-bit numbers, check bit 63
                                    if a >= (1 << 63):
                                        # This is actually a negative number in signed interpretation
                                        signed_a = a - (1 << 64)
                                        return signed_a >> b
                                    return result
                            
                            # Replace >> operations with our arithmetic shift function
                            # This is a heuristic - we'll try to evaluate and see if it works
                            try:
                                # First try normal evaluation
                                # But for complex expressions with large numbers, we need to be careful
                                # Python's eval might compute correctly, but the issue is that x86 operations
                                # work with specific bit widths (32-bit or 64-bit), and we need to simulate that
                                
                                # For expressions involving 32-bit registers (like %eax, %edx, %ecx),
                                # we need to mask intermediate results to 32 bits
                                # This is a heuristic: if the register name suggests 32-bit (ends with 'd' or 'x'),
                                # we should mask to 32 bits after operations
                                
                                # Actually, a better approach: try evaluating with bit-width constraints
                                # For now, try normal evaluation first
                                eval_result = eval(test_expr)
                                
                                # If result is suspiciously large, try masking intermediate operations
                                # This is a heuristic workaround for expressions that don't respect bit widths
                                if eval_result > (1 << 40):  # Suspiciously large for 32-bit operations
                                    # Try to mask the final result to 32 bits and check if that works
                                    eval_result_32 = eval_result & 0xffffffff
                                    # If the 32-bit result makes more sense, use it
                                    if eval_result_32 < eval_result // 1000:  # Much smaller
                                        # Try the division test with 32-bit result
                                        calculated_input_32_retry = eval_result_32 * V
                                        tolerance_32 = max(1, abs(test_input) // 20) if test_input != 0 else 1
                                        if abs(calculated_input_32_retry - test_input) <= tolerance_32:
                                            # Use the 32-bit result
                                            eval_result = eval_result_32
                                            match_count += 1
                                            continue
                                
                                # If result is suspiciously large (likely due to unsigned interpretation issues),
                                # try to interpret intermediate operations as 64-bit signed
                                if eval_result > (1 << 50):  # Suspiciously large
                                    # The expression might be computing with unsigned semantics
                                    # but we need signed semantics. However, fixing this requires
                                    # rewriting the expression evaluator, which is complex.
                                    # Instead, we'll try a workaround: check if result % (2**64) interpreted
                                    # as signed gives a reasonable value
                                    signed_result = eval_result if eval_result < (1 << 63) else eval_result - (1 << 64)
                                    # But this might not help if the intermediate operations are wrong
                                
                                expected = test_input // V if V > 0 else 0
                                
                                # For complex magic number divisions, the result might be approximate
                                # Check if result is close to expected, or if result % V == test_input % V
                                # Actually, for division, we want: result ≈ test_input / V
                                # But integer division can have rounding, so we check multiple ways
                                
                                # Method 1: Direct comparison with tolerance
                                tolerance = max(1, abs(expected) // 10) if expected != 0 else 1
                                if abs(eval_result - expected) <= tolerance:
                                    match_count += 1
                                    continue
                                
                                # Method 2: Check if result * V ≈ test_input (for positive results)
                                # This is the key test: if output = input / V, then output * V ≈ input
                                if eval_result != 0:
                                    # Calculate what input would be if result * V = input
                                    calculated_input = eval_result * V
                                    # Allow some tolerance for rounding
                                    tolerance = max(1, abs(test_input) // 20) if test_input != 0 else 1
                                    if abs(calculated_input - test_input) <= tolerance:
                                        match_count += 1
                                        continue
                                    
                                    # Also try masking result to 32 bits (for 32-bit register operations)
                                    # In x86, 32-bit register operations zero the high 32 bits
                                    result_32bit = eval_result & 0xffffffff
                                    if result_32bit != 0:
                                        calculated_input_32 = result_32bit * V
                                        if abs(calculated_input_32 - test_input) <= tolerance:
                                            match_count += 1
                                            continue
                                    
                                    # Also try with signed interpretation if result is large
                                    # For large results, they might be negative in signed interpretation
                                    if eval_result > (1 << 50):
                                        # Try interpreting as signed 64-bit
                                        signed_result = eval_result if eval_result < (1 << 63) else eval_result - (1 << 64)
                                        calculated_input_signed = signed_result * V
                                        if abs(calculated_input_signed - test_input) <= tolerance:
                                            match_count += 1
                                            continue
                                        
                                        # Also try signed 32-bit
                                        signed_result_32 = result_32bit if result_32bit < (1 << 31) else result_32bit - (1 << 32)
                                        calculated_input_signed_32 = signed_result_32 * V
                                        if abs(calculated_input_signed_32 - test_input) <= tolerance:
                                            match_count += 1
                                            continue
                                
                                # Method 3: Check if the expression represents input / V with some offset
                                # For magic number divisions, there might be a small correction term
                                # Try: result ≈ (test_input + correction) / V
                                for correction in range(-V, V + 1):
                                    if V > 0 and (test_input + correction) >= 0:
                                        approx_expected = (test_input + correction) // V
                                        if abs(eval_result - approx_expected) <= 1:
                                            match_count += 1
                                            break
                                    if match_count > 0:
                                        break
                                
                                # Method 4: Use compute_coefficient approach - if we substitute input with 1,
                                # the result should be approximately 1/V (or we can check the inverse)
                                # Actually, for division, if output = input / V, then when input = V, output = 1
                                # So we already tested that. But we can also check: when input = 1, output ≈ 1/V
                                if test_input == V and match_count == 0:
                                    # Try with input = 1 to see if result ≈ 1/V
                                    test_expr_1 = re.sub(r'\(' + re.escape(initial_reg_str) + r'\)', '(1)', expr_str)
                                    test_expr_1 = re.sub(r'\(' + re.escape(initial_reg_str) + r'\b', '(1', test_expr_1)
                                    test_expr_1 = re.sub(r'\b' + re.escape(initial_reg_str) + r'\)', '1)', test_expr_1)
                                    test_expr_1 = re.sub(r'\b' + re.escape(initial_reg_str) + r'\b', '1', test_expr_1)
                                    try:
                                        result_1 = eval(test_expr_1)
                                        # For input = 1, output should be approximately 1/V (or 0 for integer division)
                                        # Actually, for integer division, 1 / V = 0 if V > 1
                                        # So this method might not work well
                                    except:
                                        pass
                                
                                if match_count == 0:
                                    # If result is way off, it's not a division
                                    if abs(eval_result - expected) > abs(expected) // 2 and eval_result != 0:
                                        # But don't break immediately - might be a different test value
                                        pass
                            except Exception as e:
                                # If evaluation fails, skip this test value
                                # This might happen if the expression is too complex
                                continue
                        
                        # Need at least 2 matches to be confident (or 1 if only one test value worked)
                        if division_match and match_count >= min(2, len([v for v in test_values if v > 0])):
                            # Likely division relationship
                            if reg_name in register_sources:
                                output_instr_idx, direction = register_sources[reg_name]
                                output_instr = instructions[output_instr_idx]
                                if output_instr.opcode != 'mov':
                                    input_instr_idx = None
                                    for i in range(n):
                                        if instructions[i].opcode == 'mov' and \
                                           isinstance(instructions[i].operand2, str) and \
                                           instructions[i].operand2 == initial_reg:
                                            input_instr_idx = i
                                            break
                                    
                                    findings.append({
                                        'type': 'division',
                                        'line': output_instr_idx,
                                        'direction': direction,
                                        'output_instruction': instructions[output_instr_idx],
                                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                        'input_line': input_instr_idx,
                                        'description': f"Found relationship: {reg_name} = {initial_reg} / {V:#x}"
                                    })
                    except Exception as e:
                        # Silently ignore evaluation errors
                        pass
                    
                    # Try to simplify the expression and check if it equals input * V
                    # We'll try to evaluate the expression symbolically
                    # Skip if we already found a direct multiplication pattern above
                    if not (f"({initial_reg_str} * {V})" in expr_str or f"({V} * {initial_reg_str})" in expr_str or \
                           f"({initial_reg_str} * {V:#x})" in expr_str or f"({V:#x} * {initial_reg_str})" in expr_str):
                        simplified_multiple = try_simplify_to_multiple(expr_str, initial_reg_str, V)
                        if simplified_multiple is not None and simplified_multiple == V:
                            # Find the instruction that last modified this register
                            if reg_name in register_sources:
                                output_instr_idx, direction = register_sources[reg_name]
                                output_instr = instructions[output_instr_idx]
                                # Don't create relationship for mov instructions
                                if output_instr.opcode != 'mov':
                                    # Find the input instruction
                                    # First try to find mov instruction that sets initial_reg
                                    input_instr_idx = None
                                    for i in range(n):
                                        if instructions[i].opcode == 'mov' and \
                                           isinstance(instructions[i].operand2, str) and \
                                           instructions[i].operand2 == initial_reg:
                                            input_instr_idx = i
                                            break
                                    # If not found, try to find lea instruction that uses initial_reg
                                    # But don't use the same instruction as output
                                    if input_instr_idx is None:
                                        for i in range(n):
                                            if i != output_instr_idx and \
                                               instructions[i].opcode == 'lea' and \
                                               isinstance(instructions[i].operand1, str) and \
                                               initial_reg in instructions[i].operand1:
                                                input_instr_idx = i
                                                break
                                    
                                    findings.append({
                                        'type': 'multiplication',
                                        'line': output_instr_idx,
                                        'direction': direction,
                                        'output_instruction': instructions[output_instr_idx],
                                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                                        'input_line': input_instr_idx,
                                        'description': f"Found relationship: {reg_name} = {initial_reg} * {V:#x}"
                                    })
        
        # Process magic number division candidates - report only the latest one
        if magic_div_candidates:
            # Sort by instruction index (descending) to get the latest
            magic_div_candidates.sort(key=lambda x: x[1], reverse=True)
            # Report the latest one
            reg_name, _, initial_reg, _ = magic_div_candidates[0]
            relationship_key = (reg_name, str(initial_reg), V)
            if relationship_key not in found_relationships:
                # Find the last instruction that modifies this register
                output_instr_idx = None
                direction = 'forward'
                
                # Find ALL instructions that modify this register
                modifying_instrs = []
                for i in range(n):
                    instr = instructions[i]
                    if isinstance(instr.operand2, str) and instr.operand2 == reg_name:
                        modifying_instrs.append((i, instr))
                
                # Find the last arithmetic/logical operation
                last_arithmetic_instr_idx = None
                for i, instr in modifying_instrs:
                    if instr.opcode in ['add', 'sub', 'and', 'or', 'xor', 'shl', 'shr', 'sar', 'imul']:
                        last_arithmetic_instr_idx = i
                
                output_instr_idx = last_arithmetic_instr_idx if last_arithmetic_instr_idx is not None else (modifying_instrs[-1][0] if modifying_instrs else None)
                
                if output_instr_idx is not None and reg_name in register_sources:
                    _, direction = register_sources[reg_name]
                
                if output_instr_idx is not None:
                    # Find input instruction
                    input_instr_idx = None
                    for i in range(n):
                        if instructions[i].opcode == 'mov' and \
                           isinstance(instructions[i].operand2, str) and \
                           instructions[i].operand2 == initial_reg:
                            input_instr_idx = i
                            break
                    
                    findings.append({
                        'type': 'division',
                        'line': output_instr_idx,
                        'direction': direction,
                        'output_instruction': instructions[output_instr_idx],
                        'input_instruction': instructions[input_instr_idx] if input_instr_idx is not None else None,
                        'input_line': input_instr_idx,
                        'description': f"Found relationship: {reg_name} = {initial_reg} / {V:#x} (magic number division)"
                    })
                    found_relationships.add(relationship_key)
    
    def try_simplify_to_multiple(expr_str, input_reg_str, target_multiple):
        """
        Try to simplify an expression to see if it equals input * target_multiple.
        Returns the multiple if found, None otherwise.
        This is a heuristic approach that tries to identify common patterns.
        """
        # Try to evaluate the expression by substituting input_reg with 1
        # If the result equals target_multiple, then the expression equals input * target_multiple
        try:
            # Replace the input register with a variable we can evaluate
            # We'll try to parse and simplify the expression
            # For now, use a simple approach: try to match patterns
            
            # Pattern 1: Direct multiplication (input * V) or (V * input)
            if f"({input_reg_str} * {target_multiple})" in expr_str or \
               f"({target_multiple} * {input_reg_str})" in expr_str or \
               f"({input_reg_str} * {target_multiple:#x})" in expr_str or \
               f"({target_multiple:#x} * {input_reg_str})" in expr_str:
                return target_multiple
            
            # Pattern 2: Try to count operations that multiply
            # This is a simplified heuristic - count additions and shifts
            # For expressions like: (((x + x) + x) << 2) + x
            # We need to track the coefficient
            
            # A better approach: try to evaluate the expression with input=1
            # If result == target_multiple, then expression == input * target_multiple
            # But this requires a full expression evaluator
            
            # For now, let's try a pattern-based approach
            # Count how many times we add the input register
            # and track shifts that multiply
            
            # Simple heuristic: if expression contains input_reg and has operations
            # that suggest multiplication, try to compute the coefficient
            coeff = compute_coefficient(expr_str, input_reg_str)
            if coeff == target_multiple:
                return target_multiple
        except:
            pass
        return None
    
    def compute_coefficient(expr_str, input_reg_str):
        """
        Try to compute the coefficient of input_reg in the expression.
        Evaluates the expression with input_reg=1 to get the coefficient.
        """
        # Pattern: if expression is just the input register, coefficient is 1
        if expr_str.strip() == input_reg_str:
            return 1
        
        # Try to evaluate the expression by replacing input_reg with 1
        # This works if the expression is linear in input_reg
        try:
            # Replace input_reg with 1 in the expression
            # We need to be careful with string replacement
            eval_expr = expr_str.replace(input_reg_str, "1")
            # Try to evaluate it (this is safe because we control the expression format)
            # But we need to handle our expression format: (1 + 1), (1 << 2), etc.
            # Python's eval can handle this, but we need to be careful
            
            # Actually, let's try a safer approach: parse the expression manually
            # For expressions like: (((1 + 1) + 1) << 2) + 1
            # We can try to evaluate this
            
            # Replace our operators with Python operators
            eval_expr = eval_expr.replace("<<", "<<").replace(">>", ">>")
            # Try to evaluate
            result = eval(eval_expr)
            return result
        except:
            # If evaluation fails, try to parse manually
            # For now, return None
            return None
    
    # Forward search (from line_number to end)
    for i in range(line_number, n):
        execute_instruction(instructions[i], i, 'forward')
    
    # Check final relationships after forward search
    check_final_relationships()
    
    # Backward search (from line_number-1 to 0)
    # Reset registers for backward search
    registers = {}
    register_sources = {}
    for i in range(line_number - 1, -1, -1):
        execute_instruction(instructions[i], i, 'backward')
    
    # Check final relationships after backward search
    check_final_relationships()
    
    return findings

def search_value(instructions_txt, line_number, V):
    """
    User-friendly interface to search for value V starting from line_number.
    
    Args:
        instructions_txt: String containing assembly instructions
        line_number: Starting line number (0-indexed)
        V: Target value to search for (integer)
    
    Returns:
        Formatted results showing:
        - Instructions that directly use V
        - Input/output instruction relationships involving V
    """
    instructions = parse_instructions(instructions_txt)
    findings = symbolic_execute_search(instructions, line_number, V)
    
    print(f"Search value V = {V:#x} (starting from line {line_number})")
    print("=" * 60)
    
    # Group findings by type
    immediate_matches = [f for f in findings if f['type'] == 'immediate_match']
    relationships = [f for f in findings if f['type'] in ['addition', 'subtraction', 'multiplication', 'subtraction_reverse', 'value_match', 'zero_assignment', 'division', 'modulo']]
    
    if immediate_matches:
        print("\n[Instructions directly using V]")
        for f in immediate_matches:
            print(f"  Line {f['line']} ({f['direction']}): {f['instruction']}")
    
    if relationships:
        print("\n[Arithmetic/logical relationships involving V]")
        for f in relationships:
            print(f"  Relationship type: {f['type']}")
            print(f"  Output instruction (line {f['line']}, {f['direction']}): {f['output_instruction']}")
            if f.get('input_instruction') is not None:
                print(f"  Input instruction (line {f.get('input_line')}): {f['input_instruction']}")
            else:
                print(f"  Input instruction: Not found (may be initial register value)")
            print(f"  Description: {f['description']}")
            print()
    
    if not immediate_matches and not relationships:
        print("\nNo instructions or relationships found involving V")
    
    return findings

def load_test_file(test_file_path):
    """
    Load a test file where the first line contains the target value V.
    
    Args:
        test_file_path: Path to the test file
    
    Returns:
        tuple: (instructions_txt, V, line_number)
        - instructions_txt: The assembly instructions (without the first line)
        - V: Target value from first line (can be hex 0x... or decimal)
        - line_number: Starting line number (default 0)
    """
    with open(test_file_path, "r") as f:
        lines = f.readlines()
    
    if not lines:
        raise ValueError(f"Test file {test_file_path} is empty")
    
    # First line contains V
    first_line = lines[0].strip()
    
    # Parse V (can be hex 0x... or decimal)
    try:
        if first_line.startswith("0x") or first_line.startswith("0X"):
            V = int(first_line, 16)
        else:
            # Try decimal first
            V = int(first_line, 10)
    except ValueError:
        # If parsing fails, check if it looks like an instruction line
        if ":" in first_line and ("mov" in first_line or "add" in first_line or "sub" in first_line or 
                                  "xor" in first_line or "and" in first_line or "or" in first_line or
                                  "shl" in first_line or "shr" in first_line or "cmp" in first_line):
            raise ValueError(f"Test file format error: First line should be target value V (hex 0x... or decimal), but found instruction line: {first_line[:50]}...")
        else:
            raise ValueError(f"Cannot parse target value V: {first_line}. Please use hex (0x...) or decimal format")
    
    # Rest of the file contains instructions
    instructions_txt = "".join(lines[1:])
    
    # Default line_number is 0
    line_number = 0
    
    return instructions_txt, V, line_number

def run_test_file(test_file_path):
    """
    Run a single test file.
    
    Args:
        test_file_path: Path to the test file
    """
    print(f"\n{'='*60}")
    print(f"Test file: {test_file_path}")
    print(f"{'='*60}")
    
    try:
        instructions_txt, V, line_number = load_test_file(test_file_path)
        
        # Print all instructions
        print("\nAll instructions:")
        instructions = parse_instructions(instructions_txt)
        for i, instr in enumerate(instructions):
            print(f"  {i}: {instr}")
        print()
        
        # Run search
        search_value(instructions_txt, line_number, V)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def run_all_tests(tests_dir="tests"):
    """
    Run all test files in the tests directory.
    
    Args:
        tests_dir: Directory containing test files
    """
    import os
    import glob
    
    # Find all test files (test_*.txt or test_*.text)
    test_files_txt = glob.glob(os.path.join(tests_dir, "test_*.txt"))
    test_files_text = glob.glob(os.path.join(tests_dir, "test_*.text"))
    all_files = test_files_txt + test_files_text
    
    # Sort files naturally (test_1.txt, test_2.txt, ..., test_10.txt)
    # Extract number from filename for natural sorting
    def natural_sort_key(filename):
        import re
        basename = os.path.basename(filename)
        match = re.search(r'test_(\d+)', basename)
        if match:
            return int(match.group(1))
        return 0
    
    test_files = sorted(all_files, key=natural_sort_key)
    
    if not test_files:
        print(f"No test files found in {tests_dir} directory")
        return
    
    print(f"Found {len(test_files)} test files")
    
    for test_file in test_files:
        run_test_file(test_file)
        print()

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if os.path.exists(test_file):
            run_test_file(test_file)
        else:
            print(f"File does not exist: {test_file}")
    else:
        # Run all tests in tests directory
        if os.path.exists("tests"):
            run_all_tests()
        else:
            # Fallback to old behavior
            if os.path.exists("Instructions.txt"):
                with open("Instructions.txt", "r") as f:
                    instructions_txt = f.read()
                
                print("All instructions:")
                instructions = parse_instructions(instructions_txt)
                for i, instr in enumerate(instructions):
                    print(f"  {i}: {instr}")
                print()
                
                print("=" * 60)
                search_value(instructions_txt, 0, 0xd)
            else:
                print("No test files found. Usage:")
                print("  python main.py <test_file>  # Run specified test file")
                print("  python main.py              # Run all tests in tests directory")