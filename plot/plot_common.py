import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import os
import sys

colors = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#8c564b",
    "#bcbd22",
    "#7f7f7f",
    "#e377c2",
    "#17becf",
]

markers = ["o", "^", "D", "x", "P", "v", "p", "s", "h", "H"]
hatches = ["\\", "/", "|", "+", "-", ".", "*", "x", "o", "O"]
x_hatches = ["x", "xx", "xxx", "xxxx", "xxxxx", "xxxxxx", "xxxxxxx", "xxxxxxxx"]
lses = ["-", "-", "-", "-", "--", "-", "-", "-", "-", "-"]

params_line = {
    "pdf.fonttype": 42,  # make font embedded
    "axes.linewidth": 1,
    "axes.titlesize": "x-large",
    "axes.labelsize": "x-large",
    "xtick.major.size": 10,
    "xtick.major.width": 2,
    "xtick.minor.size": 5,
    "xtick.minor.width": 1,
    "ytick.major.size": 10,
    "ytick.major.width": 2,
    "ytick.minor.size": 5,
    "ytick.minor.width": 1,
    "font.size": 16,
    "font.family": "Arial",
    "xtick.labelsize": "x-large",
    "ytick.labelsize": "x-large",
    "figure.autolayout": True,
    "figure.figsize": [10, 10],
    "figure.titleweight": "bold",
    "legend.fontsize": "x-large",
    "legend.fontsize": "large",
    "legend.loc": "best",
    "legend.fancybox": False,
    "legend.frameon": False,
    "legend.handlelength": 1.0,
    "legend.handletextpad": 0.5,
    "legend.columnspacing": 1,
    "legend.borderpad": 0.1,
    "figure.dpi": 500,
    "lines.linewidth": 2,
    "lines.markersize": 10,
    "lines.markerfacecolor": "none",
    "lines.markeredgewidth": 2,
    "errorbar.capsize": 6,
    "text.antialiased": True,
    "text.hinting": "auto",
    "text.usetex": False,
}
plt.rcParams.update(params_line)

def save_fig(output_dir, fig_name, p=5):
    plt.savefig(f"{fig_name}.pdf")
    PYTHON_INTERPRETER = sys.executable
    python_interpreter = os.path.expanduser(PYTHON_INTERPRETER)
    python_interpreter_bin = os.path.dirname(python_interpreter)
    # ensure pdf-crop-margins is installed
    if not os.path.exists(f"{python_interpreter_bin}/pdf-crop-margins"):
        os.system(f"pip install pdfCropMargins")
    os.system(
        f"{python_interpreter_bin}/pdf-crop-margins -suv -p {p} -o {output_dir} {fig_name}.pdf -mo >"
        " /dev/null"
    )
    os.system(f"rm {fig_name}_uncropped.pdf > /dev/null")

def save_legend_as_figure(legend, ncol, output_dir, filename):
    
    handles = legend.legend_handles
    labels = [t.get_text() for t in legend.get_texts()]
    title = legend.get_title().get_text()
    
    fig = plt.figure(
        figsize=(1, 1), 
        dpi=legend.axes.figure.dpi,
        layout="tight"
    )
    
    new_legend = fig.legend(
        handles=handles,
        labels=labels,
        title=title,
        ncol=ncol,
        bbox_to_anchor=(0.5, 0.5),
        loc='center',
        handlelength=2,
        fontsize=20,
        labelspacing=0.5
    )
    
    for new_text, orig_text in zip(new_legend.get_texts(), legend.get_texts()):
        new_text.set_fontproperties(orig_text.get_fontproperties().copy())
    new_legend.get_title().set_fontproperties(
        legend.get_title().get_fontproperties().copy()
    )
    
    fig.canvas.draw()
    bbox = new_legend.get_tightbbox(fig.canvas.renderer)
    fig.set_size_inches(bbox.width/fig.dpi + 0.5, bbox.height/fig.dpi + 0.5)
    
    save_fig(output_dir, filename + "_legend")
    plt.close(fig)