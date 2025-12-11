# In[1]:

#!/usr/bin/env python3

import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

latex_macros = []

skip_macro_list = [
    # Huge IR diff
    'MLD_MAX_QUEUE',
    'MAX_MADVISE_GUARD_RETRIES',
    'MAX_VMAP_RETRIES',
    'TCP_DELACK_MAX',

    # Not in all-cases.txt
    'Try_KLP_bad_case',
]

# In[2]:


analysis_time_csv_file = 'kernel-results/overhead.csv'

df = pd.read_csv(analysis_time_csv_file)

if df.shape[1] < 3:
    print("CSV must have at least 3 columns")
    sys.exit(1)

# Remove rows where the first column matches any skip macro

# print(f"Original {len(df)} cases")

pattern = re.compile(r'^kernel-results/([^/]+)/')
def is_skip_macro(row):
    m = pattern.match(str(row.iloc[0]))
    if m:
        macro_name = m.group(1)
        return macro_name in skip_macro_list
    return False

df = df[~df.apply(is_skip_macro, axis=1)].reset_index(drop=True)

# print(f"Original {len(df)} cases")

analysis_time_minutes = df.iloc[:, 1]

analysis_time_minutes_mean = analysis_time_minutes.mean()
analysis_time_minutes_stddev = analysis_time_minutes.std()
analysis_time_minutes_max = analysis_time_minutes.max()

idx_analysis_time_minutes_max = analysis_time_minutes.idxmax()
max_analysis_time_file_name = df.iloc[idx_analysis_time_minutes_max, 0].strip()
max_analysis_time_macro_name = max_analysis_time_file_name.split('/')[1].strip()
max_analysis_time_macro_name_latex = str(max_analysis_time_macro_name).replace('_', '\\_')
max_analysis_time_macro_name_latex = f"\\texttt{{{max_analysis_time_macro_name_latex}}}"
with open(Path(max_analysis_time_file_name).parent / 'ss-size2.txt', 'r') as f:
    content = f.read()
    total_instructions = re.search(r'Total: (\d+) instructions', content).group(1)
    total_instructions = int(total_instructions)
    max_analysis_time_instructions = total_instructions
    max_analysis_time_instructions_str = "{:,.0f}".format(max_analysis_time_instructions)

analysis_time_minutes_mean_str = "{:.0f}".format(analysis_time_minutes_mean)
analysis_time_minutes_stddev_str = "{:.0f}".format(analysis_time_minutes_stddev)
analysis_time_minutes_max_str = "{:.0f}".format(analysis_time_minutes_max)

latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsAnalysisTimeMean}}{{{analysis_time_minutes_mean_str}\\xspace}}")
latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsAnalysisTimeStddev}}{{{analysis_time_minutes_stddev_str}\\xspace}}")
latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsAnalysisTimeMax}}{{{analysis_time_minutes_max_str}\\xspace}}")

latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsAnalysisTimeMaxMacro}}{{{max_analysis_time_macro_name_latex}\\xspace}}")
latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsAnalysisTimeMaxInstructions}}{{{max_analysis_time_instructions_str}\\xspace}}")

df = pd.read_csv('kernel-results/per-perf-const-size.txt')
ss_size_median = df.iloc[:, 0].median()
ss_size_median_str = "{:,.0f}".format(ss_size_median)

latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsSizeMedian}}{{{ss_size_median_str}\\xspace}}")

# In[4]:

with open('kernel-results/per-perf-const-size.txt', 'r') as f:
    content = f.read()

with open('paper-assets/ss_instr_size.txt', 'w') as f:
    f.write(content)

print("Don't forget to move ss_instr_size.txt to plot repo ./cs_ss_func_size/")

# In[5]:

import glob

count_disjoint_sses = {}

for filename in glob.glob('kernel-results/*/ss-size2.txt'):
    skip=False
    for skip_macro in skip_macro_list:
        if filename == f'kernel-results/{skip_macro}/ss-size2.txt':
            skip=True
            break

    if skip:
        continue

    with open(filename) as f:
        # Number of spans with largest L value
        bb_lines = [line for line in f if 'BB' in line]
        count_disjoint_sses[filename] = len(bb_lines)

with open('paper-assets/disjoint_sses.txt', 'w') as f:
    for fname, count in count_disjoint_sses.items():
        f.write(f"{count}\n")

print("Don't forget to move disjoint_sses.txt to plot repo ./dataset/")

# In[6]:

with open('find-binary-addresses/disjoint_sses_asm.txt', 'r') as f:
    content = f.read()

with open('paper-assets/disjoint_sses_asm.txt', 'w') as f:
    f.write(content)

print("Don't forget to move disjoint_sses_asm.txt to plot repo ./dataset/")

# In[7]:

with open('paper-assets/disjoint_sses_asm.txt', 'r') as f:
    total = 0
    for line in f:
        line = line.strip()
        if line:
            total += int(line)
    latex_macros.append(f"\\newcommand{{\\wentaoNumbersNumDisjointSsAsm}}{{{total}\\xspace}}")

with open('paper-assets/disjoint_sses.txt', 'r') as f:
    total = 0
    for line in f:
        line = line.strip()
        if line:
            total += int(line)
    latex_macros.append(f"\\newcommand{{\\wentaoNumbersNumDisjointSsIr}}{{{total}\\xspace}}")

# In[8]:

input_spans_total = 0
output_clusters_total = 0
input_files_total = 0
reduction_total = 0
file_reduction_total = 0
has_reduction_total = 0

for f in glob.glob('kernel-results/*/ss-size1.txt'):
    with open(f, 'r') as f2:
        my_label = f.split('/')[1]
        if my_label in skip_macro_list:
            continue
        for line in f2:
            if "Reduction: " in line:
                reduction_total += int(line.split(" ")[1])
            elif "Total input spans: " in line:
                input_spans_total += int(line.split(" ")[3])
            elif "Total output clusters: " in line:
                output_clusters_total += int(line.split(" ")[3])
            elif "Input files: " in line:
                input_files_total += int(line.split(" ")[2])
            elif "File reduction: " in line:
                file_reduction_total += int(line.split(" ")[2])
                if int(line.split(" ")[2]) > 0:
                    has_reduction_total += 1

latex_macros.append(f"\\newcommand{{\\wentaoNumbersSsReduction}}{{{file_reduction_total}\\xspace}}")
latex_macros.append(f"\\newcommand{{\\wentaoNumbersNumPerfConstsWithSsReduction}}{{{has_reduction_total}\\xspace}}")

# In[9]:

with open('TaintTrackerPass.cpp', 'r') as f:
    total = 0
    for line in f:
        line = line.strip()
        if line:
            total += 1
    total = "{:,.0f}".format(total)
    latex_macros.append(f"\\newcommand{{\\wentaoNumbersNumLinesLlvmPass}}{{{total}\\xspace}}")

# In[10]:

import os
import csv

input_data = 'cs.csv'

zj_keys = set()
cs_num = {}

with open('paper-assets/cs.csv', 'r') as f:
    lines = f.readlines()
    csv_reader = csv.reader(lines)
    for row in csv_reader:
        key = row[0]
        zj_keys.add(key)
        cs_num[key] = int(row[1])

import glob

translate_label = {
    'ca__delay_min': 'ca->delay_min >> 3',
    'delta__4': 'delta *= 4;',
    'delta__freeable__2': 'delta = freeable / 2;',
    'group_faults': 'group_faults(p, dst_nid) * 4',
    'node_stamp__2__TICK_NSEC': 'p->node_stamp += 2 * TICK_NSEC;',
    'node_stamp__32__diff': 'p->node_stamp += 32 * diff;',
    'numa_scan_seq': 'p->numa_scan_seq <= 4',
    'tcp_min_rtt': 'tcp_min_rtt(tp) >> 2',
}

ss_reduce = {}

for f in glob.glob('kernel-results/*/ss-size1.txt'):
    my_label = f.split('/')[1]
    if my_label in skip_macro_list:
        continue
    if my_label in translate_label:
        my_label = translate_label[my_label]
    assert my_label in zj_keys, f"Key {my_label} not found in zj_keys"
    with open(f, 'r') as f2:
        for line in f2:
            if 'files merged into groups' in line:
                ss_reduce[my_label] = int(line.strip().split()[2])

with open('paper-assets/disjoint_sses_xyz.txt', 'w') as f:
    for my_label, count in ss_reduce.items():
        xyz_count = max(cs_num[my_label] - ss_reduce[my_label], 1)
        f.write(f"{xyz_count}\n")

print("Don't forget to move disjoint_sses_xyz.txt to plot repo ./dataset/")

# In[3]:

with open('paper-assets/numbers_auto.tex', 'w') as f:
    f.write("""% Autogenerated. Do not modify by hand.
% https://github.com/zhongjiechen/Xkernel/tree/dataflow/paper-assets

""")
    f.write("\n".join(latex_macros))
    f.write("\n")

print("Don't forget to move numbers_auto.tex to the LaTeX repo ./Data/eval_wentao/")

