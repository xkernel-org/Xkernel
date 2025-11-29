#!/usr/bin/env python3

"""
Run the analysis for all kernel-results/*.input.txt files in parallel
"""

import os
import sys
import glob
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import Tuple, Optional

def log_info(msg: str):
    """Print info message"""
    print(f"[INFO] {msg}")

def log_success(msg: str):
    """Print success message"""
    print(f"[SUCCESS] {msg}")

def log_error(msg: str):
    """Print error message"""
    print(f"[ERROR] {msg}", file=sys.stderr)

def log_warning(msg: str):
    """Print warning message"""
    print(f"[WARNING] {msg}")

def check_prerequisites(kernel_dir: Path) -> bool:
    """Check if all prerequisites are met"""
    if not kernel_dir.exists():
        log_error(f"KERNEL_DIR does not exist: {kernel_dir}")
        return False
    return True

def parse_input_file(input_file: Path) -> dict:
    """Parse the input file to extract variables"""
    variables = {}
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                # Simple parsing for bash variable assignments
                key, value = line.split('=', 1)
                # Remove inline comments (everything after #)
                if '#' in value:
                    value = value.split('#', 1)[0]
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                variables[key] = value
    return variables

def process_input_file(args: Tuple[Path, int, int, str, dict]) -> Tuple[str, bool, Optional[str]]:
    """
    Process a single input file

    Args:
        args: Tuple of (input_file, current_index, total, date_start, config)

    Returns:
        Tuple of (input_file_str, success, error_message)
    """
    input_file, current, total, date_start, config = args

    kernel_dir = Path(config['kernel_dir'])

    interproc = config['interproc']
    upward_interproc = config['upward_interproc']
    indirect_call = config['indirect_call']
    # whole_kernel = config['whole_kernel']

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_info(f"[{current}/{total}] {input_file}, {date_start} -> {now}")

    try:
        # Parse input file
        variables = parse_input_file(input_file)

        source_file = variables.get('SOURCE_FILE', '')
        function_name = variables.get('FUNCTION_NAME', '')
        source_op = variables.get('SOURCE_OP', '')
        constant_value = variables.get('CONSTANT_VALUE', '')
        occurrence = variables.get('OCCURENCE', '')

        # Setup output files
        output_file = input_file.parent / f"{input_file.stem.replace('.input', '')}.output.txt"
        time_statistics = input_file.parent / f"{input_file.stem.replace('.input', '')}.time.txt"

        # Skip if output file already exists
        if output_file.exists():
            log_info(f"[{current}/{total}] Skipping {input_file} - output already exists")
            return (str(input_file), True, None)

        # Setup bitcode files
        source_path = Path(source_file)
        # obj_file = source_path.with_suffix('.o')
        # bc_file = source_path.with_suffix('.bc')
        ll_file = source_path.with_suffix('.ll')
        vmlinux_bc = kernel_dir / 'vmlinux.bc'

        # Compile if not using whole kernel
        # if not whole_kernel:
        #     os.chdir(kernel_dir)
        #     if obj_file.exists():
        #         obj_file.unlink()
        #
        #     make_cmd = [
        #         'make',
        #         'CC=wllvm',
        #         'AR=llvm-ar',
        #         'HOSTCC=clang',
        #         str(obj_file)
        #     ]
        #     subprocess.run(make_cmd, check=True, capture_output=True)
        #
        #     extract_cmd = ['extract-bc', str(obj_file), '-o', str(bc_file)]
        #     subprocess.run(extract_cmd, check=True, capture_output=True)
        #
        #     llvm_dis_cmd = ['llvm-dis', str(bc_file), '-o', str(ll_file)]
        #     subprocess.run(llvm_dis_cmd, check=True, capture_output=True)

        # Determine input BC file
        # if whole_kernel:
        #     input_bc_file = vmlinux_bc
        # else:
        #     input_bc_file = kernel_dir / bc_file

        input_bc_file = vmlinux_bc

        # Build the opt command
        pass_args = f"{function_name};{source_op};{constant_value};false;{interproc};{indirect_call};{upward_interproc};{occurrence}"
        opt_cmd = [
            '/usr/bin/time', '-o', str(time_statistics), '-v',
            'opt',
            '-load-pass-plugin=build/libTaintTrackerPass.so',
            f'-passes=taint-tracker<{pass_args}>',
            '-disable-output',
            str(input_bc_file)
        ]

        # Run the analysis
        with open(output_file, 'w') as out_f:
            result = subprocess.run(
                opt_cmd,
                stdout=out_f,
                stderr=subprocess.STDOUT,
                cwd=config['cwd']
            )

            # Append additional info
            out_f.write(f"\n{kernel_dir / ll_file}\n")
            out_f.write(f"{kernel_dir / source_file}\n")

        if result.returncode != 0:
            return (str(input_file), False, f"opt command failed with exit code {result.returncode}")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_success(f"[{current}/{total}] Completed {input_file} at {now}")
        return (str(input_file), True, None)

    except Exception as e:
        return (str(input_file), False, str(e))

def main():
    parser = argparse.ArgumentParser(
        description='Run kernel analysis in parallel on multiple input files'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=30,
        help=f'Number of parallel jobs (default: 30)'
    )
    parser.add_argument(
        '--kernel-dir',
        type=str,
        default=os.environ.get('KERNEL_DIR', '../linux-wllvm-defconfig'),
        help='Path to kernel directory (default: $KERNEL_DIR or ../linux-wllvm-defconfig)'
    )
    parser.add_argument(
        '--no-interproc',
        action='store_true',
        help='Disable interprocedural analysis'
    )
    parser.add_argument(
        '--no-upward-interproc',
        action='store_true',
        help='Disable upward interprocedural analysis'
    )
    parser.add_argument(
        '--no-indirect-call',
        action='store_true',
        help='Disable indirect call analysis'
    )
    # parser.add_argument(
    #     '--no-whole-kernel',
    #     action='store_true',
    #     help='Compile individual files instead of using whole kernel'
    # )

    args = parser.parse_args()

    # Setup environment
    # os.environ['LLVM_COMPILER'] = 'clang'

    kernel_dir = Path(args.kernel_dir)

    # Check prerequisites
    if not check_prerequisites(kernel_dir):
        return 1

    # Find all input files
    input_pattern = 'kernel-results/*/*.input.txt'
    input_files = sorted(glob.glob(input_pattern))

    if not input_files:
        log_error(f"No input files found matching {input_pattern}")
        return 1

    total = len(input_files)
    log_info(f"Found {total} input files to process")
    log_info(f"Using {args.jobs} parallel jobs")

    # Configuration
    config = {
        'kernel_dir': str(kernel_dir),
        'interproc': 'true' if not args.no_interproc else 'false',
        'upward_interproc': 'true' if not args.no_upward_interproc else 'false',
        'indirect_call': 'true' if not args.no_indirect_call else 'false',
        # 'whole_kernel': not args.no_whole_kernel,
        'cwd': os.getcwd()
    }

    date_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nStarting parallel processing at {date_start}\n")

    # Prepare arguments for each job
    job_args = [
        (Path(input_file), idx + 1, total, date_start, config)
        for idx, input_file in enumerate(input_files)
    ]

    # Process in parallel
    results = []
    failed = []

    with Pool(processes=args.jobs) as pool:
        for result in pool.imap_unordered(process_input_file, job_args):
            results.append(result)
            input_file, success, error_msg = result
            if not success:
                failed.append((input_file, error_msg))

    date_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Print summary
    print(f"\n{'=' * 80}")
    print(f"All jobs completed!")
    print(f"Started:  {date_start}")
    print(f"Finished: {date_end}")
    print()

    success_count = len(results) - len(failed)

    if failed:
        log_warning("Failed jobs:")
        for input_file, error_msg in failed:
            print(f"  {input_file}")
            if error_msg:
                print(f"    {error_msg}")

    print()
    print(f"Summary: {success_count} succeeded, {len(failed)} failed out of {total} total")
    print('=' * 80)

    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
