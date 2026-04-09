#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize benchmark results by computing averages across repeats.

Reads the "=== Results ===" blocks from a benchmark output file and appends
averaged metrics (throughput, latency percentiles, migration stats) at the end.

Usage:
    python plot/summarize.py results/20251126/32.txt
"""
import re
import sys
import collections
import argparse


def calculate_and_append_averages(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return

    data = collections.defaultdict(list)

    result_blocks = re.findall(
        r'=== Results ===(.*?)(?=\[start\] residency|Done!)',
        content, re.DOTALL
    )

    if not result_blocks:
        print("No '=== Results ===' sections found in the file.")
        return

    for block in result_blocks:
        total_ops = re.search(r'Total ops: (\d+)', block)
        if total_ops:
            data['Total ops'].append(int(total_ops.group(1)))

        query_throughput = re.search(r'Query throughput: ([\d.]+)', block)
        if query_throughput:
            data['Query throughput'].append(float(query_throughput.group(1)))

        migration_calls = re.search(r'Migration calls: (\d+)', block)
        if migration_calls:
            data['Migration calls'].append(int(migration_calls.group(1)))

        avg_migration_latency = re.search(r'Avg migration latency: ([\d.]+) ms', block)
        if avg_migration_latency:
            data['Avg migration latency'].append(float(avg_migration_latency.group(1)))

        per_successful_page_latency = re.search(r'Per-successful-page latency: ([\d.]+) us/page', block)
        if per_successful_page_latency:
            data['Per-successful-page latency'].append(float(per_successful_page_latency.group(1)))

        pages_migrated = re.search(r'Pages migrated \(succ/fail\): (\d+) / (\d+)', block)
        if pages_migrated:
            data['Pages migrated - succ'].append(int(pages_migrated.group(1)))
            data['Pages migrated - fail'].append(int(pages_migrated.group(2)))

        page_migration_throughput = re.search(r'Page migration throughput: ([\d.]+) pages/s', block)
        if page_migration_throughput:
            data['Page migration throughput'].append(float(page_migration_throughput.group(1)))

        qps_window = re.search(
            r'QPS window.*?min=([\d.]+) p50=([\d.]+) p90=([\d.]+) p95=([\d.]+) p99=([\d.]+) max=([\d.]+)',
            block
        )
        if qps_window:
            data['QPS min'].append(float(qps_window.group(1)))
            data['QPS p50'].append(float(qps_window.group(2)))
            data['QPS p90'].append(float(qps_window.group(3)))
            data['QPS p95'].append(float(qps_window.group(4)))
            data['QPS p99'].append(float(qps_window.group(5)))
            data['QPS max'].append(float(qps_window.group(6)))

        probe_latency = re.search(
            r'Probe latency.*?min=([\d.]+) p50=([\d.]+) p90=([\d.]+) p95=([\d.]+) p99=([\d.]+) max=([\d.]+)',
            block
        )
        if probe_latency:
            data['Probe min'].append(float(probe_latency.group(1)))
            data['Probe p50'].append(float(probe_latency.group(2)))
            data['Probe p90'].append(float(probe_latency.group(3)))
            data['Probe p95'].append(float(probe_latency.group(4)))
            data['Probe p99'].append(float(probe_latency.group(5)))
            data['Probe max'].append(float(probe_latency.group(6)))

    averages = {key: sum(values) / len(values) for key, values in data.items() if values}

    output = "\n\n************************************\n\n"
    output += f"Total ops, {averages.get('Total ops', 0):,.0f}\n"
    output += f"Query throughput, {averages.get('Query throughput', 0) / 1000:,.2f} Kops/s\n"
    output += f"Migration calls, {averages.get('Migration calls', 0):.1f}\n"
    output += f"Avg migration latency, {averages.get('Avg migration latency', 0):.2f} ms\n"
    output += f"Per-successful-page latency, {averages.get('Per-successful-page latency', 0):.2f} μs/page\n"
    output += f"Pages migrated - succ, {averages.get('Pages migrated - succ', 0):,.0f}\n"
    output += f"Pages migrated - fail, {averages.get('Pages migrated - fail', 0):,.0f}\n"
    output += f"Page migration throughput, {averages.get('Page migration throughput', 0):,.1f} pages/s\n\n"
    output += "************************************\n\n"
    output += "QPS (10ms)\n"
    output += f"min, {averages.get('QPS min', 0):,.0f} ops/s\n"
    output += f"P50, {averages.get('QPS p50', 0):,.0f} ops/s\n"
    output += f"P90, {averages.get('QPS p90', 0):,.0f} ops/s\n"
    output += f"P95, {averages.get('QPS p95', 0):,.0f} ops/s\n"
    output += f"P99, {averages.get('QPS p99', 0):,.0f} ops/s\n"
    output += f"max, {averages.get('QPS max', 0):,.0f} ops/s\n\n"
    output += "************************************\n\n"
    output += "Probe Lantency N=2000 ops\n"
    output += f"min, {averages.get('Probe min', 0):.2f} μs\n"
    output += f"P50, {averages.get('Probe p50', 0):.2f} μs\n"
    output += f"P90, {averages.get('Probe p90', 0):.2f} μs\n"
    output += f"P95, {averages.get('Probe p95', 0):.2f} μs\n"
    output += f"P99, {averages.get('Probe p99', 0):.2f} μs\n"
    output += f"max, {averages.get('Probe max', 0):.2f} μs\n"

    try:
        with open(file_path, 'a') as f:
            f.write(output)
        print(f"Averages appended to '{file_path}'.")
    except IOError as e:
        print(f"Error writing to file '{file_path}': {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Calculate and append averages from benchmark output.'
    )
    parser.add_argument('file_path', type=str, help='Path to the result .txt file')
    args = parser.parse_args()

    calculate_and_append_averages(args.file_path)
