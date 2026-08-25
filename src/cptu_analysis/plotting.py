"""Publication-oriented CPTu profile figures."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from .core import IC_BOUNDS, SOIL_CLASS_NAMES, layer_table, soil_class

COLORS = ("#e9b878", "#e7cf91", "#a9d7bf", "#77b5aa", "#8791aa", "#c98e78")


def _curve(ax, depth, ic, title):
    ax.plot(ic, depth, color="#111820", lw=1.15)
    for boundary in IC_BOUNDS:
        ax.axvline(boundary, color="#9aaab2", ls="--", lw=.8)
    ax.set(xlim=(.5, 4.5), xlabel="$I_c$", title=title)
    ax.grid(axis="y", color="#dfe7ea", lw=.7)


def _log(ax, depth, ic, title):
    for layer in layer_table(depth, soil_class(ic)):
        ax.axhspan(layer["top_m"], layer["base_m"], color=COLORS[layer["class"]], ec="#263238", lw=.5)
    ax.set(xlim=(0, 1), xticks=[], title=title)


def save_profile_figure(depth, raw, smooth, profile_id, destination):
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 11, "axes.labelcolor": "#334a55"})
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 8), sharey=True,
                             gridspec_kw={"width_ratios": [2.2, 1, 2.2, 1]})
    _curve(axes[0], depth, raw, "Original $I_c$")
    _log(axes[1], depth, raw, "Original SBTn")
    _curve(axes[2], depth, smooth, "Smoothed $I_c$ ($\\sigma=0.05$ m)")
    _log(axes[3], depth, smooth, "Smoothed SBTn")
    axes[0].set_ylabel("Depth (m)")
    axes[0].invert_yaxis()
    fig.suptitle(f"CPTu soil behaviour profile | ID {profile_id}", x=.06, ha="left", fontsize=15, weight="bold")
    fig.legend([Patch(fc=c, ec="#263238") for c in COLORS], SOIL_CLASS_NAMES,
               loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, .11, 1, .95))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=220, facecolor="white")
    plt.close(fig)
