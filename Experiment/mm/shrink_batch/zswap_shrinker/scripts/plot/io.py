import os
import re
import matplotlib.pyplot as plt
import numpy as np
import sys

DEFAULT_DIRECTORY = '/users/yltang/Xkernel/Experiment/shrink_batch/zswap_shrinker/res/dt_us'

def parse_files(directory):
    if not directory:
        directory = DEFAULT_DIRECTORY

    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist.")
        sys.exit(1)

    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    files.sort(key=lambda f: int(re.sub(r'\D', '', f)))

    elapsed_times = []
    inputs = []
    filenames = []

    elapsed_pattern = r'(\d+:\d+\.\d+)elapsed'
    inputs_pattern = r'(\d+)inputs'

    for filename in files:
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                if len(lines) < 2:
                    print(f"Warning: {filename} has fewer than 2 lines, skipped.")
                    continue

                second_last_line = lines[-2]
                last_line = lines[-1]

                elapsed_match = re.search(elapsed_pattern, second_last_line)
                inputs_match = re.search(inputs_pattern, last_line)

                if elapsed_match and inputs_match:
                    elapsed_times.append(elapsed_match.group(1))
                    inputs.append(int(inputs_match.group(1)))
                    filenames.append(filename[:-4])  # 去掉 .txt
                else:
                    print(f"Error: Could not parse required data in {filename}.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return filenames, elapsed_times, inputs

def plot_data(filenames, elapsed_times, inputs, output_pdf):
    elapsed_seconds = []
    for time_str in elapsed_times:
        mins, secs = map(float, time_str.split(':'))
        elapsed_seconds.append(mins * 60 + secs)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.bar(filenames, inputs, color='b', alpha=0.6, label='block I/O (read)', width=0.6)
    ax1.set_xlabel('SHRINK_BATCH')
    ax1.set_ylabel('block I/O (read)', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(filenames, elapsed_seconds, color='r', marker='o', label='Elapsed Time (seconds)')
    ax2.set_ylabel('Elapsed Time (seconds)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.legend(loc='upper right')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig(output_pdf, format='pdf')
    print(f"Figure saved as {output_pdf}")
    plt.close(fig)

def main(directory=None, output_pdf='io.pdf'):
    filenames, elapsed_times, inputs = parse_files(directory)
    if filenames:
        plot_data(filenames, elapsed_times, inputs, output_pdf)
    else:
        print("No .txt files found or no data to plot.")

if __name__ == "__main__":
    # python3 script.py [directory] [output_pdf]
    directory = sys.argv[1] if len(sys.argv) > 1 else None
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else 'io.pdf'
    main(directory, output_pdf)