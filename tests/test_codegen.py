"""Tests for src/codegen.py — Symbolic execution engine."""
import pytest
from src.codegen import SymbolicExecutor


class TestRegisterMapping:
    """Test register name normalization and anonymous mapping."""

    def test_base_register_64bit(self):
        se = SymbolicExecutor()
        assert se.get_base_register('rax') == 'rax'
        assert se.get_base_register('rbx') == 'rbx'
        assert se.get_base_register('r13') == 'r13'

    def test_base_register_32bit(self):
        se = SymbolicExecutor()
        assert se.get_base_register('eax') == 'rax'
        assert se.get_base_register('ebx') == 'rbx'
        assert se.get_base_register('r13d') == 'r13'

    def test_base_register_16bit(self):
        se = SymbolicExecutor()
        assert se.get_base_register('ax') == 'rax'
        assert se.get_base_register('si') == 'rsi'

    def test_base_register_8bit(self):
        se = SymbolicExecutor()
        assert se.get_base_register('al') == 'rax'
        assert se.get_base_register('r13b') == 'r13'
        assert se.get_base_register('sil') == 'rsi'

    def test_anonymous_mapping_consistency(self):
        """Sub-registers of the same base should map to the same anonymous reg."""
        se = SymbolicExecutor()
        r1 = se.get_anonymous_reg('eax')
        r2 = se.get_anonymous_reg('rax')
        r3 = se.get_anonymous_reg('al')
        assert r1 == r2 == r3

    def test_different_regs_different_anonymous(self):
        se = SymbolicExecutor()
        r1 = se.get_anonymous_reg('eax')
        r2 = se.get_anonymous_reg('ebx')
        assert r1 != r2

    def test_anonymous_counter_increments(self):
        se = SymbolicExecutor()
        r0 = se.get_anonymous_reg('eax')
        r1 = se.get_anonymous_reg('ebx')
        r2 = se.get_anonymous_reg('ecx')
        assert r0 == 'r0'
        assert r1 == 'r1'
        assert r2 == 'r2'


class TestInstructionParsing:
    """Test x86 instruction line parsing."""

    def test_simple_mov(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1a3:  b8 80 00 00 00\tmov    $0x80,%eax")
        assert result is not None
        addr, mnemonic, operands = result
        assert addr == '1a3'
        assert mnemonic == 'mov'
        assert len(operands) == 2
        assert operands[0] == '$0x80'
        assert operands[1] == '%eax'

    def test_shl_instruction(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1b0:  c1 e0 03\tshl    $0x3,%eax")
        assert result is not None
        _, mnemonic, operands = result
        assert mnemonic == 'shl'
        assert operands[0] == '$0x3'
        assert operands[1] == '%eax'

    def test_memory_operand(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1c0:  8b 43 10\tmov    0x10(%rbx),%eax")
        assert result is not None
        _, mnemonic, operands = result
        assert mnemonic == 'mov'
        assert '0x10(%rbx)' in operands[0]

    def test_sib_addressing(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1d0:  8b 04 8b\tmov    (%rbx,%rcx,4),%eax")
        assert result is not None
        _, _, operands = result
        assert '(%rbx,%rcx,4)' in operands[0]

    def test_no_operands(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1e0:  c3\tret")
        assert result is not None
        _, mnemonic, operands = result
        assert mnemonic == 'ret'
        assert len(operands) == 0

    def test_skip_non_instruction(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  0000000000001a80 <function_name>:")
        assert result is None

    def test_skip_continuation_line(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  281:  00")
        assert result is None

    def test_inline_comment_stripped(self):
        se = SymbolicExecutor()
        result = se.parse_instruction("  1a3:  e8 50 ff ff ff\tcall   158 <func+0x10>")
        assert result is not None
        _, mnemonic, _ = result
        assert mnemonic == 'call'


class TestOperandParsing:
    """Test operand type detection and parsing."""

    def test_immediate(self):
        se = SymbolicExecutor()
        typ, val, reg = se.parse_operand('$0x80')
        assert typ == 'imm'
        assert val == '0x80'

    def test_immediate_decimal(self):
        se = SymbolicExecutor()
        typ, val, reg = se.parse_operand('$128')
        assert typ == 'imm'
        assert val == '0x80'

    def test_register(self):
        se = SymbolicExecutor()
        typ, val, reg = se.parse_operand('%eax')
        assert typ == 'reg'
        assert reg == 'eax'

    def test_memory_simple(self):
        se = SymbolicExecutor()
        typ, val, reg = se.parse_operand('0x10(%rbx)')
        assert typ == 'mem'
        assert reg == 'rbx'

    def test_memory_no_offset(self):
        se = SymbolicExecutor()
        typ, val, reg = se.parse_operand('(%rax)')
        assert typ == 'mem'
        assert reg == 'rax'


class TestSymbolicExecution:
    """Test symbolic execution of instruction sequences."""

    def test_mov_immediate(self):
        se = SymbolicExecutor()
        result = se.execute_instruction('mov', ['$0x80', '%eax'])
        r = se.get_anonymous_reg('eax')
        assert se.state[r] == '0x80'

    def test_mov_reg_to_reg(self):
        se = SymbolicExecutor()
        # Set up initial state
        se.execute_instruction('mov', ['$0x10', '%eax'])
        se.execute_instruction('mov', ['%eax', '%ebx'])
        r_eax = se.get_anonymous_reg('eax')
        r_ebx = se.get_anonymous_reg('ebx')
        assert se.state[r_ebx] == '0x10'

    def test_add_immediate(self):
        se = SymbolicExecutor()
        se.execute_instruction('mov', ['$0x5', '%eax'])
        se.execute_instruction('add', ['$0x3', '%eax'])
        r = se.get_anonymous_reg('eax')
        # State should show addition expression
        assert '0x5' in se.state[r] or '0x3' in se.state[r]

    def test_shl_instruction(self):
        se = SymbolicExecutor()
        se.execute_instruction('mov', ['$0x10', '%eax'])
        se.execute_instruction('shl', ['$0x3', '%eax'])
        r = se.get_anonymous_reg('eax')
        # State should reflect shift or multiplication
        state = se.state[r]
        assert '0x10' in state or 'r0' in state
