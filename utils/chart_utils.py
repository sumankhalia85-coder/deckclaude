"""
DeckClaude Chart Utilities — Consulting-style matplotlib chart helpers.

Provides:
  - consulting_style(ax, fig): Apply minimal McKinsey-style aesthetics
  - color_palette(n, theme): Brand-consistent color list
  - save_chart(fig, name, output_dir): Save with consistent DPI and settings
  - format_axis_labels(ax, axis, scale): Format as 1M, 1B, 1K etc.
  - add_value_labels(ax, bars, fmt): Add value annotations above/beside bars
  - add_trend_annotation(ax, x, y, text): Add a callout annotation to chart
  - multi_bar_chart(categories, series_data, ...): Quick multi-series bar chart
  - sparkline(values, ...): Minimal inline sparkline chart
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output")) / "charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_theme_colors(theme_name: str = "default") -> dict:
    """Load brand colors from brand_config.json."""
    config_path = Path(__file__).parent.parent / "config" / "brand_config.json"
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        return cfg.get("themes", {}).get(theme_name, cfg.get("themes", {}).get("default", {}))
    except Exception:
        return {
            "primary_color": "#002060",
            "secondary_color": "#00B0F0",
            "accent_color": "#FF6B35",
        }


def _load_chart_colors() -> List[str]:
    config_path = Path(__file__).parent.parent / "config" / "brand_config.json"
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        return cfg.get("chart_colors", ["#002060", "#00B0F0", "#FF6B35", "#70AD47", "#FFC000", "#7030A0"])
    except Exception:
        return ["#002060", "#00B0F0", "#FF6B35", "#70AD47", "#FFC000", "#7030A0"]


CHART_COLORS = _load_chart_colors()


def color_palette(n: int, theme: str = "default") -> List[str]:
    """
    Return a list of n brand-consistent hex color strings.
    Cycles through the brand palette if n exceeds palette size.

    Args:
        n: Number of colors needed
        theme: Brand theme name ('default', 'mckinsey', 'dark_tech', 'consulting_green')

    Returns:
        List of '#RRGGBB' hex strings, length n
    """
    theme_data = _load_theme_colors(theme)
    base_colors = [
        theme_data.get("primary_color", "#002060"),
        theme_data.get("secondary_color", "#00B0F0"),
        theme_data.get("accent_color", "#FF6B35"),
    ] + CHART_COLORS[3:]

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in base_colors:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    # Cycle to fill n
    return [unique[i % len(unique)] for i in range(n)]


def consulting_style(ax, fig=None, title_color: str = "#1A1A2E", grid_axis: str = "y"):
    """
    Apply McKinsey/consulting-style minimal chart aesthetics.

    Removes: top and right spines, tick marks, heavy gridlines.
    Keeps: bottom and left spines (thin, light), y-gridlines (dashed, very light).

    Args:
        ax: matplotlib Axes object
        fig: matplotlib Figure object (optional, for background)
        title_color: Color for the chart title
        grid_axis: 'y' | 'x' | 'both' | 'none'
    """
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    ax.tick_params(axis="both", which="both", length=0, labelsize=9, colors="#444444")
    ax.tick_params(axis="x", pad=4)
    ax.tick_params(axis="y", pad=4)

    if grid_axis != "none":
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.4, color="#EEEEEE", alpha=0.9)
    ax.set_axisbelow(True)

    if fig:
        fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Style title if present
    title = ax.get_title()
    if title:
        ax.title.set_fontsize(13)
        ax.title.set_fontweight("bold")
        ax.title.set_color(title_color)
        ax.title.set_pad(14)


def format_value(val: float) -> str:
    """
    Format a numeric value for axis labels.
    1_200_000 → '1.2M', 5_400 → '5.4K', 0.042 → '4.2%' (only for 0-1 range)

    Args:
        val: Numeric value to format

    Returns:
        Formatted string
    """
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)

    if abs(v) >= 1_000_000_000:
        return f"{v / 1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if abs(v) >= 10_000:
        return f"{v / 1_000:.0f}K"
    if abs(v) >= 1_000:
        return f"{v / 1_000:.1f}K"
    if abs(v) < 1 and v != 0:
        return f"{v * 100:.1f}%"
    return f"{v:.0f}" if v == int(v) else f"{v:.1f}"


def format_axis_labels(ax, axis: str = "y", scale: str = "auto"):
    """
    Apply formatted number labels to an axis.

    Args:
        ax: matplotlib Axes
        axis: 'x' | 'y' | 'both'
        scale: 'auto' | 'millions' | 'thousands' | 'billions' | 'percent'
    """
    def auto_formatter(x, pos):
        return format_value(x)

    def millions_formatter(x, pos):
        return f"{x / 1_000_000:.1f}M"

    def thousands_formatter(x, pos):
        return f"{x / 1_000:.0f}K"

    def billions_formatter(x, pos):
        return f"{x / 1_000_000_000:.1f}B"

    def pct_formatter(x, pos):
        return f"{x:.0f}%"

    formatters = {
        "auto": auto_formatter,
        "millions": millions_formatter,
        "thousands": thousands_formatter,
        "billions": billions_formatter,
        "percent": pct_formatter,
    }
    fn = mticker.FuncFormatter(formatters.get(scale, auto_formatter))

    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(fn)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(fn)


def add_value_labels(
    ax,
    bars,
    fmt: str = "auto",
    color: str = "#333333",
    fontsize: int = 8,
    padding_pct: float = 0.01,
    horizontal: bool = False,
):
    """
    Add value labels above (or beside for horizontal) each bar.

    Args:
        ax: matplotlib Axes
        bars: BarContainer from ax.bar() or ax.barh()
        fmt: 'auto' | 'percent' | 'millions' | custom format string
        color: Label text color
        fontsize: Label font size
        padding_pct: Offset as fraction of axis range
        horizontal: True for horizontal bars
    """
    if horizontal:
        xlim = ax.get_xlim()
        x_range = xlim[1] - xlim[0]
        for bar in bars:
            val = bar.get_width()
            label = format_value(val) if fmt == "auto" else f"{val:{fmt}}"
            ax.text(
                val + x_range * padding_pct,
                bar.get_y() + bar.get_height() / 2,
                label,
                va="center", ha="left", fontsize=fontsize, color=color,
            )
    else:
        ylim = ax.get_ylim()
        y_range = ylim[1] - ylim[0]
        for bar in bars:
            val = bar.get_height()
            label = format_value(val) if fmt == "auto" else f"{val:{fmt}}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + y_range * padding_pct,
                label,
                ha="center", va="bottom", fontsize=fontsize, color=color,
            )


def add_trend_annotation(
    ax,
    x,
    y,
    text: str,
    arrow_color: str = "#FF6B35",
    text_color: str = "#333333",
    fontsize: int = 8,
    box_style: str = "round,pad=0.3",
):
    """
    Add a callout annotation with an arrow pointing to a data point.

    Args:
        ax: matplotlib Axes
        x, y: Data coordinates to point at
        text: Annotation text
        arrow_color: Color of the annotation arrow
        text_color: Color of the annotation text
        fontsize: Font size of annotation text
        box_style: Matplotlib boxstyle string
    """
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(x, y * 1.15),
        fontsize=fontsize,
        color=text_color,
        ha="center",
        arrowprops=dict(
            arrowstyle="->",
            color=arrow_color,
            lw=1.0,
            connectionstyle="arc3,rad=0.1",
        ),
        bbox=dict(boxstyle=box_style, facecolor="white", edgecolor=arrow_color, alpha=0.8),
    )


def save_chart(fig, name: str, output_dir: Optional[Union[str, Path]] = None, dpi: int = 150) -> str:
    """
    Save a matplotlib figure as a PNG with consistent settings.

    Args:
        fig: matplotlib Figure
        name: Filename (with or without .png extension)
        output_dir: Directory to save in (defaults to OUTPUT_DIR)
        dpi: Resolution (150 is good for PowerPoint insertion)

    Returns:
        Absolute path string of saved file
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not name.endswith(".png"):
        name += ".png"

    path = output_dir / name
    fig.savefig(str(path), dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    logger.debug(f"Chart saved: {path}")
    return str(path)


def multi_bar_chart(
    categories: List[str],
    series_data: Dict[str, List[float]],
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    theme: str = "default",
    figsize: Tuple[float, float] = (9, 5.5),
    output_name: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a grouped multi-series bar chart with brand styling.

    Args:
        categories: X-axis category labels
        series_data: {series_name: [values...]} dict
        title: Chart title
        x_label/y_label: Axis labels
        theme: Brand theme name
        figsize: Figure dimensions in inches
        output_name: If provided, save chart and return path

    Returns:
        (fig, ax) tuple
    """
    colors = color_palette(len(series_data), theme)
    n_cats = len(categories)
    n_series = len(series_data)
    x = np.arange(n_cats)
    bar_width = 0.75 / n_series

    fig, ax = plt.subplots(figsize=figsize)

    for i, (series_name, values) in enumerate(series_data.items()):
        offset = (i - n_series / 2 + 0.5) * bar_width
        bars = ax.bar(
            x + offset, values, bar_width * 0.9,
            label=series_name, color=colors[i], edgecolor="white", linewidth=0.3,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=0 if n_cats <= 8 else 30, ha="right")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
    ax.set_xlabel(x_label, fontsize=10, color="#333333")
    ax.set_ylabel(y_label, fontsize=10, color="#333333")
    ax.legend(fontsize=9, frameon=False, loc="upper right")
    format_axis_labels(ax, "y")
    consulting_style(ax, fig)
    plt.tight_layout(pad=1.5)

    return fig, ax


def sparkline(
    values: List[float],
    color: str = "#002060",
    figsize: Tuple[float, float] = (2.0, 0.6),
    fill: bool = True,
) -> plt.Figure:
    """
    Generate a minimal inline sparkline chart (no axes, no labels).
    Suitable for embedding in tables or summary boxes.

    Args:
        values: Data values for the sparkline
        color: Line color
        figsize: Figure size (should be small)
        fill: Whether to fill area under the line

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("none")
    ax.set_facecolor("none")

    x = np.arange(len(values))
    ax.plot(x, values, color=color, linewidth=1.5)
    if fill:
        ax.fill_between(x, values, alpha=0.15, color=color)

    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig


def percent_change_indicator(
    current: float,
    previous: float,
    label: str = "",
    positive_is_good: bool = True,
) -> Tuple[str, str]:
    """
    Calculate percent change and return (formatted_value, color_hex) tuple.
    Used for KPI cards and data callouts.

    Args:
        current: Current period value
        previous: Prior period value
        label: Optional metric label for logging
        positive_is_good: Whether an increase is favorable (green) or unfavorable (red)

    Returns:
        (formatted_pct_string, color_hex) e.g. ('+12.4%', '#70AD47')
    """
    if previous == 0:
        return ("N/A", "#888888")

    pct = (current - previous) / abs(previous) * 100
    sign = "+" if pct >= 0 else ""
    formatted = f"{sign}{pct:.1f}%"

    if positive_is_good:
        color = "#70AD47" if pct >= 0 else "#FF6B35"
    else:
        color = "#FF6B35" if pct >= 0 else "#70AD47"

    return (formatted, color)
