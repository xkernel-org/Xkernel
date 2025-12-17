# Unit Tests for check_assembly_diff.py

This directory contains unit tests for the `check_assembly_diff.py` script.

## Structure

- `cmd.sh`: Single file containing all test commands, each marked with `# TEST N:`
- `res_*.txt`: Result files, containing step 11 output from the corresponding test command
- `gen.sh`: Script to generate/update result files

## Usage

1. Add test commands to `cmd.sh` file (one command per line):
   ```bash
   sudo python /users/chenzj/Xkernel/check_assembly_diff.py -f block/blk-mq.c -s "BLK_MAX_REQUEST_COUNT" "64"
   sudo python /users/chenzj/Xkernel/check_assembly_diff.py -f net/ipv4/tcp_output.c -s "TCP_MAXSEG" "1460"
   ```

2. Run `gen.sh` to execute all test commands and extract step 11 output:
   ```bash
   ./gen.sh
   ```

3. The script will:
   - Read `cmd.sh` line by line
   - Execute each command (automatically numbered)
   - Extract only step 11 output (Basic Block extraction)
   - Save the output to corresponding `res_*.txt` files

## File Format

- `cmd.sh`: One command per line
  - Empty lines and lines starting with `#` are ignored
  - Commands are automatically numbered (first command = TEST 1, second = TEST 2, etc.)
- `res_N.txt`: Contains step 11 output for the Nth command in `cmd.sh`

