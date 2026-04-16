#!/usr/bin/env python3
"""Plot Figure 18: Transition time comparison — KLP vs XKernel.

Reads transition time measurements from results/ and produces a bar chart
showing that KLP transition takes seconds/minutes while XKernel's per-thread
mode completes in milliseconds.

Usage:
    python3 plot/plot.py                    # auto-detect results/
    python3 plot/plot.py path/to/results    # specific results dir
"""
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_common


def load_times(filepath):
    """Load transition times (in nanoseconds) from a results file."""
    times = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                times.append(int(line))
            except ValueError:
                continue
    return np.array(times)


def plot_figure18(results_dir):
    klp_file = os.path.join(results_dir, 'klp_times.txt')
    xk_file = os.path.join(results_dir, 'xkernel_times.txt')

    for f in [klp_file, xk_file]:
        if not os.path.exists(f):
            print(f"[skip] {f} not found")
            return

    klp_ns = load_times(klp_file)
    xk_ns = load_times(xk_file)

    # Convert to seconds
    klp_s = klp_ns / 1e9
    xk_s = xk_ns / 1e9

    print(f"\n=== Transition Times ===")
    print(f"KLP:     median={np.median(klp_s):.3f}s, "
          f"mean={np.mean(klp_s):.3f}s, "
          f"min={np.min(klp_s):.3f}s, max={np.max(klp_s):.3f}s")
    print(f"XKernel: median={np.median(xk_s):.6f}s, "
          f"mean={np.mean(xk_s):.6f}s, "
          f"min={np.min(xk_s):.6f}s, max={np.max(xk_s):.6f}s")
    print(f"Speedup: {np.median(klp_s) / np.median(xk_s):.0f}x (median)")

    # ── Bar chart ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(1, 1, figsize=(5, 4))

    methods = ['KLP', 'XKernel\n(per-thread)']
    medians = [np.median(klp_s), np.median(xk_s)]
    errors_lo = [np.median(klp_s) - np.min(klp_s),
                 np.median(xk_s) - np.min(xk_s)]
    errors_hi = [np.max(klp_s) - np.median(klp_s),
                 np.max(xk_s) - np.median(xk_s)]

    bar_colors = ['#B0B0B0', '#2ca02c']
    bars = ax.bar(methods, medians, color=bar_colors, edgecolor='black',
                  linewidth=1.2, width=0.5, zorder=3)

    ax.errorbar(methods, medians, yerr=[errors_lo, errors_hi],
                fmt='none', ecolor='black', capsize=5, linewidth=1.5,
                zorder=4)

    ax.set_yscale('log')
    ax.set_ylabel('Transition Time (s)', fontsize=18)
    ax.tick_params(axis='both', labelsize=16)

    # Add value labels on bars
    for bar, med in zip(bars, medians):
        if med >= 1.0:
            label = f'{med:.1f}s'
        elif med >= 0.001:
            label = f'{med*1000:.0f}ms'
        else:
            label = f'{med*1e6:.0f}µs'
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.5,
                label, ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.3, axis='y', linestyle='--', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    plot_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(plot_dir, 'figure18')
    print(f"\n[ok] Plot saved to {plot_dir}/figure18.pdf")
    plt.close()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = os.path.join(script_dir, '..', 'results')

    results_dir = os.path.abspath(results_dir)
    print(f"Using results from: {results_dir}")
    plot_figure18(results_dir)
