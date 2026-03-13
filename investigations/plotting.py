from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = REPO_ROOT / ".tmp"
MATPLOTLIB_DIR = TMP_DIR / "matplotlib"
MATPLOTLIB_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(TMP_DIR))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


COLOR_NAVY = "#1f3b5c"
COLOR_BLUE = "#4e79a7"
COLOR_TEAL = "#2f6f6f"
COLOR_GOLD = "#b8860b"
COLOR_RED = "#9c3d2e"
COLOR_SLATE = "#6b7785"
COLOR_GRID = "#d9dee5"
PALETTE = [COLOR_NAVY, COLOR_BLUE, COLOR_TEAL, COLOR_GOLD, COLOR_RED, COLOR_SLATE]


def apply_plot_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#8a94a3",
            "axes.linewidth": 0.8,
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "semibold",
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "font.size": 10,
            "grid.color": COLOR_GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.75,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def style_axis(ax: Axes, *, x_grid: bool = False, y_grid: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y" if y_grid else "x", visible=y_grid or x_grid)
    if x_grid and y_grid:
        ax.grid(axis="x", visible=True)
    elif x_grid:
        ax.grid(axis="x", visible=True)
        ax.grid(axis="y", visible=False)
    elif not y_grid:
        ax.grid(False)


def save_figure(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
