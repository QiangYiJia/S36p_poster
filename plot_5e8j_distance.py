#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CLUSTER_DIR = Path("/Users/2648471/Documents/cluster")
OUT_DIR = Path("/Users/2648471/Documents/S36p_poster/draft_figures")

BASE = "5E8J"
LIGAND = "SAM_GTG"
REP = 3
RESIDUES = ["H439", "K442"]
MA_WINDOW = 50
TOTAL_NS = 500.0

DISPLAY_ORDER = ["WT(S36)", "S36D", "S36E", "S36p"]
DISPLAY_TO_TAG = {"WT(S36)": "WT", "S36D": "S36D", "S36E": "S36E", "S36p": "S36p"}
COLORS = {
    "WT(S36)": "tab:green",
    "S36D": "tab:orange",
    "S36E": "tab:red",
    "S36p": "tab:blue",
}


def moving_average(data: np.ndarray, window: int) -> np.ndarray:
    data = np.asarray(data, dtype=float)
    weights = np.ones(window, dtype=float)
    numerator = np.convolve(data, weights, mode="same")
    denominator = np.convolve(np.ones_like(data), weights, mode="same")
    return numerator / denominator


def load_distance(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path, comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    frames = data[:, 0].astype(float)
    distances = data[:, -1].astype(float)
    times = (frames - frames.min()) / (frames.max() - frames.min()) * TOTAL_NS
    return times, distances


def plot_residue(residue: str) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    y_values: list[float] = []
    max_time = TOTAL_NS

    for display in DISPLAY_ORDER:
        tag = DISPLAY_TO_TAG[display]
        path = CLUSTER_DIR / f"{BASE}_{tag}_{LIGAND}_{REP}_{residue}.dat"
        if not path.exists():
            raise FileNotFoundError(path)

        times, distances = load_distance(path)
        ma = moving_average(distances, MA_WINDOW)
        color = COLORS[display]

        ax.plot(times, distances, linestyle="--", alpha=0.20, linewidth=1.1, color=color)
        ax.plot(times, ma, linewidth=2.1, color=color, label=display)

        means[display] = float(np.nanmean(distances))
        stds[display] = float(np.nanstd(distances, ddof=0))
        y_values.extend([float(np.nanmin(distances)), float(np.nanmax(distances))])
        max_time = max(max_time, float(np.nanmax(times)))

    for display in DISPLAY_ORDER:
        ax.axhline(
            means[display],
            linestyle="--",
            linewidth=0.9,
            color=COLORS[display],
            alpha=0.9,
        )

    ymin = min(y_values)
    ymax = max(y_values)
    pad = (ymax - ymin) * 0.08
    ymin = max(0.0, ymin - pad)
    ymax = ymax + pad
    ax.set_ylim(ymin, ymax)

    label_gap = (ymax - ymin) * 0.080
    label_margin = (ymax - ymin) * 0.035
    placed: list[float] = []

    for display, mean_value in sorted(means.items(), key=lambda item: item[1], reverse=True):
        label_y = mean_value
        for existing_y in placed:
            if abs(label_y - existing_y) < label_gap:
                label_y = existing_y - label_gap
        label_y = max(ymin + label_margin, min(ymax - label_margin, label_y))
        placed.append(label_y)

        ax.plot(
            [max_time * 0.98, max_time],
            [mean_value, mean_value],
            linestyle=":",
            linewidth=1.0,
            color=COLORS[display],
            alpha=0.8,
        )

        ax.annotate(
            f"{display} d={mean_value:.2f}±{stds[display]:.1f} Å",
            xy=(1.0, (label_y - ymin) / (ymax - ymin)),
            xytext=(-6, 0),
            textcoords="offset points",
            xycoords=("axes fraction", "axes fraction"),
            ha="right",
            va="center",
            fontsize=12,
            color=COLORS[display],
            bbox=dict(
                boxstyle="round,pad=0.20",
                fc="white",
                ec=COLORS[display],
                alpha=0.65,
                linewidth=1.2,
            ),
        )

    ax.set_xlim(-15, TOTAL_NS + 25)
    ax.set_xticks([0, 100, 200, 300, 400, 500])
    ax.set_xlabel("Time (ns)", fontsize=26, labelpad=12)
    ax.set_ylabel("Distance (Å)", fontsize=26, labelpad=10)
    ax.tick_params(axis="both", labelsize=21, width=1.4, length=7)

    for spine in ax.spines.values():
        spine.set_linewidth(1.4)

    legend = ax.legend(
        loc="upper left",
        fontsize=14,
        frameon=True,
        framealpha=0.92,
        borderpad=0.35,
        labelspacing=0.35,
        handlelength=1.8,
        handletextpad=0.6,
    )
    legend.get_frame().set_edgecolor("#b0b0b0")
    legend.get_frame().set_linewidth(1.1)

    fig.subplots_adjust(left=0.18, right=0.965, bottom=0.24, top=0.96)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{BASE}_{LIGAND}_S36_{residue}_rep{REP}_poster.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def main() -> None:
    for residue in RESIDUES:
        print(plot_residue(residue))


if __name__ == "__main__":
    main()
