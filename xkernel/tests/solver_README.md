# Symbolic Execution Based Value Search

This tool performs symbolic execution on x86-64 assembly instructions to find relationships involving a target value `V`. It can detect:

1. **Direct usage**: Instructions that directly use the value `V` as an immediate operand
2. **Arithmetic/logical relationships**: Complex relationships where `V` is implicitly involved, such as:
   - Multiplication: `output = input * V`
   - Division: `output = input / V`
   - Addition/Subtraction: `output = input +/- V`
   - Zero assignment: `output = 0` (when `V = 0`)
   - Modulo: `output = input % V`

## Algorithm Overview

### Core Components

1. **Instruction Parsing**: Parses AT&T syntax assembly instructions from text format
   - Extracts opcode, operand1, and operand2
   - Handles immediate values (prefixed with `$`) and converts them to integers
   - Supports complex address expressions (e.g., `lea (%rdx,%rdx,4),%rcx`)

2. **Symbolic Execution**: Tracks register values as symbolic expressions
   - Uses `SymbolicExpr` class to represent register values as expressions
   - Supports arithmetic operations: `+`, `-`, `*`, `&`, `|`, `^`, `<<`, `>>`
   - Performs forward and backward execution from a given line number

3. **Relationship Detection**: Identifies relationships involving the target value `V`
   - **Immediate value detection**: Checks if any instruction directly uses `V`
   - **Pattern-based detection**: Recognizes common compiler optimizations:
     - Magic number divisions (complex division using multiplication and shifts)
     - Multiplication via `lea` and `shl` combinations
     - Division via `sar`/`shr` instructions
     - Zero assignment via `xor %reg, %reg`

### Key Features

#### Magic Number Division Detection

The algorithm can detect complex division operations that compilers generate using "magic numbers". These typically involve:
- Large constant multiplication (`imul` with magic number)
- Right shifts to extract high bits
- Addition/subtraction for correction terms
- Sign correction for signed divisions

The algorithm:
1. Detects patterns containing large constants (8+ digits) combined with shifts
2. Checks if expressions reference registers containing magic numbers
3. Handles 32-bit/64-bit register name mapping (e.g., `%edx` ↔ `%rdx`)
4. Collects all candidate registers and selects the one modified latest (final result)
5. Finds the final arithmetic instruction that completes the computation

#### Register State Tracking

- Maintains a `registers` dictionary mapping register names to their symbolic values
- Tracks which instruction last modified each register (`register_sources`)
- Identifies initial input registers (from memory loads or simple register assignments)

#### Expression Evaluation

- Uses heuristic evaluation with multiple test values to verify relationships
- Handles bit-width constraints (32-bit vs 64-bit operations)
- Supports signed/unsigned interpretation for large numbers
- Uses tolerance-based matching for complex expressions

### Supported Instructions

- **Data movement**: `mov`, `movslq`, `movsx`, `movs`
- **Arithmetic**: `add`, `sub`, `imul` (2 and 3 operand forms)
- **Logical**: `and`, `or`, `xor`
- **Shifts**: `shl`, `sal`, `shr`, `sar`
- **Address calculation**: `lea`
- **Comparison**: `cmp`, `sbb`

### Usage

```bash
# Run a specific test file
python main.py tests/test_13.txt

# Run all tests in tests directory
python main.py
```

### Test File Format

Each test file should have:
- **First line**: Target value `V` (hex `0x...` or decimal)
- **Remaining lines**: Assembly instructions in AT&T syntax

Example (`tests/test_13.txt`):
```
127
115c:       8b 45 f8                mov    -0x8(%rbp),%eax
115f:       48 63 d0                movslq %eax,%rdx
1162:       48 69 d2 09 04 02 81    imul   $0xffffffff81020409,%rdx,%rdx
...
```

### Output Format

The tool outputs:
- **Direct usage**: Instructions that directly use `V`
- **Relationships**: Arithmetic/logical relationships involving `V`, including:
  - Relationship type (multiplication, division, etc.)
  - Output instruction (the instruction that produces the result)
  - Input instruction (the instruction that provides the input)
  - Description of the relationship

Example output:
```
[Arithmetic/logical relationships involving V]
  Relationship type: division
  Output instruction (line 9, forward): sub %ecx %eax
  Input instruction (line 0): mov -0x8(%rbp) %eax
  Description: Found relationship: %eax = %eax / 0x7f (magic number division)
```

### Algorithm Limitations

1. **Expression complexity**: Very complex expressions may not be correctly evaluated
2. **Bit-width simulation**: Some edge cases in 32-bit/64-bit register operations may not be perfectly simulated
3. **Magic number detection**: Relies on pattern matching and heuristic evaluation, may miss some edge cases
4. **Instruction support**: Only supports a subset of x86-64 instructions

### Implementation Details

- **SymbolicExpr**: Represents symbolic expressions as strings, overloads arithmetic operators
- **Forward/Backward search**: Executes instructions in both directions from a starting line
- **Final relationship check**: After execution, analyzes final register states to find relationships
- **Natural sorting**: Test files are sorted naturally (e.g., `test_10.txt` comes after `test_9.txt`)

