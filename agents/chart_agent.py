"""
ChartGeneratorAgent — Generates publication-quality matplotlib charts with brand styling.
Supports: bar, line, stacked_bar, pie, waterfall, funnel, scatter charts.
Applies consulting aesthetics: minimal gridlines, clean labels, no chart junk.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


def _load_brand_colors() -> list:
    config_path = Path(__file__).parent.parent / "config" / "brand_config.json"
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config.get("chart_colors", ["#002060", "#00B0F0", "#FF6B35", "#70AD47", "#FFC000", "#7030A0"])
    except Exception:
        return ["#002060", "#00B0F0", "#FF6B35", "#70AD47", "#FFC000", "#7030A0"]


BRAND_COLORS = _load_brand_colors()


def consulting_style(ax, fig=None):
    """Apply McKinsey-style minimal chart aesthetics."""
    import matplotlib.pyplot as plt
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(axis="both", which="both", length=0, labelsize=9, colors="#444444")
    ax.grid(axis="y", linestyle="--", linewidth=0.4, color="#EEEEEE", alpha=0.8)
    ax.set_axisbelow(True)
    if fig:
        fig.patch.set_facecolor("white")
    ax.set_facecolor("white")


def format_value(val) -> str:
    """Format large numbers for axis labels: 1000000 → '1M', 1000 → '1K'."""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if abs(v) >= 1_000_000_000:
        return f"{v / 1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"{v / 1_000:.1f}K"
    if isinstance(val, float) and not val.is_integer():
        return f"{v:.1f}"
    return f"{int(v)}"


class ChartGeneratorAgent(BaseAgent):
    """
    Generates branded matplotlib charts and saves them as PNG files.

    Input state keys:
        slide_contents (list): Per-slide content from InsightGeneratorAgent
        intent_spec (dict): For theme color selection
        output_dir (str): Directory to save chart PNGs

    Output (AgentResult.data):
        {
          chart_files: {slide_number: {path, chart_type, title, metadata}}
        }
    """

    def __init__(self):
        super().__init__(
            name="ChartGeneratorAgent",
            description="Generates consulting-style matplotlib charts as PNG files",
        )
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output")) / "charts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_theme_colors(self, theme: str = "default") -> list:
        config_path = Path(__file__).parent.parent / "config" / "brand_config.json"
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            theme_data = config.get("themes", {}).get(theme, {})
            primary = theme_data.get("primary_color", "#002060")
            secondary = theme_data.get("secondary_color", "#00B0F0")
            accent = theme_data.get("accent_color", "#FF6B35")
            return [primary, secondary, accent] + BRAND_COLORS[3:]
        except Exception:
            return BRAND_COLORS

    def _safe_filename(self, text: str, slide_num: int) -> str:
        safe = re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")[:40]
        return f"slide_{slide_num:02d}_{safe}.png"

    def generate_bar_chart(
        self, data_points: list, title: str, x_label: str, y_label: str,
        colors: list, slide_num: int, horizontal: bool = False
    ) -> str:
        """Grouped bar chart, horizontal or vertical."""
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        labels = [str(d.get("label", f"Item {i+1}")) for i, d in enumerate(data_points)]
        values = [float(d.get("value", 0)) for d in data_points]
        bar_colors = [colors[i % len(colors)] for i in range(len(labels))]

        fig, ax = plt.subplots(figsize=(9, 5.5))
        if horizontal:
            bars = ax.barh(labels, values, color=bar_colors, edgecolor="none", height=0.6)
            ax.set_xlabel(y_label, fontsize=10, color="#333333")
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
            for bar, val in zip(bars, values):
                ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                        format_value(val), va="center", ha="left", fontsize=8.5, color="#333333")
        else:
            bars = ax.bar(labels, values, color=bar_colors, edgecolor="none", width=0.65)
            ax.set_ylabel(y_label, fontsize=10, color="#333333")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        format_value(val), ha="center", va="bottom", fontsize=8.5, color="#333333")

        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        consulting_style(ax, fig)
        plt.tight_layout(pad=1.5)

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_line_chart(
        self, data_points: list, title: str, x_label: str, y_label: str,
        colors: list, slide_num: int
    ) -> str:
        """Line chart — supports single series (list of {label, value})
        or multi-series (list of {label, series: {name: value}})."""
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        fig, ax = plt.subplots(figsize=(9, 5.5))

        if data_points and isinstance(data_points[0].get("value"), (int, float)):
            # Single series
            labels = [str(d.get("label", i)) for i, d in enumerate(data_points)]
            values = [float(d.get("value", 0)) for d in data_points]
            ax.plot(labels, values, color=colors[0], linewidth=2.5, marker="o",
                    markersize=5, markerfacecolor="white", markeredgewidth=1.5)
            ax.fill_between(range(len(labels)), values, alpha=0.08, color=colors[0])
            # Rotate labels if many
            if len(labels) > 8:
                plt.xticks(rotation=45, ha="right")
        else:
            # Multi-series: data_points = [{label: "Q1", series: {Revenue: 100, Cost: 80}}]
            labels = [str(d.get("label", i)) for i, d in enumerate(data_points)]
            if data_points and "series" in data_points[0]:
                series_names = list(data_points[0]["series"].keys())
                for idx, sname in enumerate(series_names):
                    values = [float(d["series"].get(sname, 0)) for d in data_points]
                    ax.plot(labels, values, color=colors[idx % len(colors)], linewidth=2,
                            marker="o", markersize=4, label=sname)
                ax.legend(fontsize=9, frameon=False)
            if len(labels) > 8:
                plt.xticks(rotation=45, ha="right")

        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        ax.set_xlabel(x_label, fontsize=10, color="#333333")
        ax.set_ylabel(y_label, fontsize=10, color="#333333")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
        consulting_style(ax, fig)
        plt.tight_layout(pad=1.5)

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_stacked_bar_chart(
        self, data_points: list, title: str, x_label: str, y_label: str,
        colors: list, slide_num: int
    ) -> str:
        """Stacked bar chart. data_points: [{label, series: {cat1: val, cat2: val}}]"""
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np

        fig, ax = plt.subplots(figsize=(9, 5.5))

        labels = [str(d.get("label", i)) for i, d in enumerate(data_points)]
        # Determine categories
        if data_points and "series" in data_points[0]:
            categories = list(data_points[0]["series"].keys())
        else:
            # Fallback: treat each data point as single category
            ax.bar(labels, [float(d.get("value", 0)) for d in data_points], color=colors[0])
            ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
            consulting_style(ax, fig)
            plt.tight_layout(pad=1.5)
            path = self.output_dir / self._safe_filename(title, slide_num)
            fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            return str(path)

        x = np.arange(len(labels))
        bottoms = np.zeros(len(labels))

        for idx, cat in enumerate(categories):
            vals = np.array([float(d["series"].get(cat, 0)) for d in data_points])
            ax.bar(x, vals, bottom=bottoms, label=cat, color=colors[idx % len(colors)],
                   edgecolor="white", linewidth=0.5, width=0.65)
            bottoms += vals

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0 if len(labels) <= 8 else 45, ha="right")
        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        ax.set_xlabel(x_label, fontsize=10, color="#333333")
        ax.set_ylabel(y_label, fontsize=10, color="#333333")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
        ax.legend(fontsize=9, frameon=False, loc="upper right")
        consulting_style(ax, fig)
        plt.tight_layout(pad=1.5)

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_pie_chart(
        self, data_points: list, title: str, colors: list, slide_num: int
    ) -> str:
        """Donut-style pie chart with percentage labels."""
        import matplotlib.pyplot as plt

        labels = [str(d.get("label", f"Item {i+1}")) for i, d in enumerate(data_points)]
        values = [abs(float(d.get("value", 0))) for d in data_points]
        if not any(values):
            values = [1.0] * len(values)

        pie_colors = [colors[i % len(colors)] for i in range(len(labels))]
        fig, ax = plt.subplots(figsize=(7.5, 5.5))

        wedges, texts, autotexts = ax.pie(
            values, labels=None, colors=pie_colors, autopct="%1.1f%%",
            startangle=90, pctdistance=0.75,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")

        # Draw a white circle for donut effect
        centre_circle = plt.Circle((0, 0), 0.55, fc="white")
        ax.add_patch(centre_circle)

        ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.1),
                  ncol=min(3, len(labels)), fontsize=9, frameon=False)
        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        fig.patch.set_facecolor("white")
        plt.tight_layout()

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_waterfall_chart(
        self, data_points: list, title: str, x_label: str, y_label: str,
        colors: list, slide_num: int
    ) -> str:
        """Waterfall chart for financial bridge analysis."""
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np

        labels = [str(d.get("label", f"Item {i+1}")) for i, d in enumerate(data_points)]
        values = [float(d.get("value", 0)) for d in data_points]

        running = 0.0
        bottoms = []
        bar_colors = []
        for i, val in enumerate(values):
            if i == 0 or i == len(values) - 1:
                bottoms.append(0)
                bar_colors.append(colors[0])
            elif val >= 0:
                bottoms.append(running)
                bar_colors.append("#70AD47")  # green for increase
            else:
                bottoms.append(running + val)
                bar_colors.append("#FF6B35")  # orange-red for decrease
            running += val

        fig, ax = plt.subplots(figsize=(9, 5.5))
        x = np.arange(len(labels))
        ax.bar(x, [abs(v) for v in values], bottom=bottoms, color=bar_colors,
               edgecolor="white", linewidth=0.5, width=0.65)

        # Connector lines
        cum = 0.0
        for i, val in enumerate(values):
            if i < len(values) - 1 and i != 0:
                ax.plot([i - 0.325, i + 0.325], [cum, cum], color="#999999",
                        linewidth=0.8, linestyle="--")
            cum += val

        # Value labels
        for i, (val, bot) in enumerate(zip(values, bottoms)):
            ax.text(i, bot + abs(val) + max(abs(v) for v in values) * 0.01,
                    format_value(val), ha="center", fontsize=8.5, color="#333333")

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0 if len(labels) <= 8 else 45, ha="right")
        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        ax.set_xlabel(x_label, fontsize=10, color="#333333")
        ax.set_ylabel(y_label, fontsize=10, color="#333333")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
        consulting_style(ax, fig)
        plt.tight_layout(pad=1.5)

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_funnel_chart(
        self, data_points: list, title: str, colors: list, slide_num: int
    ) -> str:
        """Funnel chart for conversion analysis."""
        import matplotlib.pyplot as plt
        import numpy as np

        labels = [str(d.get("label", f"Stage {i+1}")) for i, d in enumerate(data_points)]
        values = [abs(float(d.get("value", 0))) for d in data_points]
        max_val = max(values) if values else 1

        fig, ax = plt.subplots(figsize=(7, 6))
        bar_height = 0.6
        y_positions = np.arange(len(labels) - 1, -1, -1)

        for i, (label, val) in enumerate(zip(labels, values)):
            width = val / max_val
            left = (1 - width) / 2
            color = colors[i % len(colors)]
            ax.barh(y_positions[i], width, left=left, height=bar_height,
                    color=color, edgecolor="white", linewidth=1)
            ax.text(0.5, y_positions[i], f"{label}: {format_value(val)}",
                    ha="center", va="center", fontsize=9, color="white", fontweight="bold")

        # Conversion rates
        for i in range(len(values) - 1):
            if values[i] > 0:
                rate = values[i + 1] / values[i] * 100
                ax.text(1.02, (y_positions[i] + y_positions[i + 1]) / 2,
                        f"{rate:.0f}%", va="center", fontsize=8, color="#666666")

        ax.set_xlim(0, 1.15)
        ax.set_ylim(-0.5, len(labels) - 0.5)
        ax.axis("off")
        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        fig.patch.set_facecolor("white")
        plt.tight_layout()

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_scatter_chart(
        self, data_points: list, title: str, x_label: str, y_label: str,
        colors: list, slide_num: int
    ) -> str:
        """Scatter plot with optional bubble sizes."""
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        x_vals = [float(d.get("x", d.get("value", 0))) for d in data_points]
        y_vals = [float(d.get("y", d.get("value2", d.get("value", 0)))) for d in data_points]
        sizes = [float(d.get("size", 80)) for d in data_points]
        pt_colors = [colors[i % len(colors)] for i in range(len(data_points))]
        labels = [str(d.get("label", "")) for d in data_points]

        fig, ax = plt.subplots(figsize=(9, 5.5))
        sc = ax.scatter(x_vals, y_vals, s=sizes, c=pt_colors, alpha=0.8, edgecolors="white", linewidths=0.5)

        for i, label in enumerate(labels):
            if label:
                ax.annotate(label, (x_vals[i], y_vals[i]),
                            textcoords="offset points", xytext=(4, 4),
                            fontsize=7.5, color="#333333")

        ax.set_title(title, fontsize=13, fontweight="bold", color="#1A1A2E", pad=14)
        ax.set_xlabel(x_label, fontsize=10, color="#333333")
        ax.set_ylabel(y_label, fontsize=10, color="#333333")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_value(x)))
        consulting_style(ax, fig)
        plt.tight_layout(pad=1.5)

        path = self.output_dir / self._safe_filename(title, slide_num)
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(path)

    def generate_chart(self, slide_num: int, visual_data: dict, theme: str = "default") -> Optional[str]:
        """
        Dispatch to the appropriate chart generator based on chart_type.
        Returns the file path of the generated PNG, or None if generation fails.
        """
        chart_type = visual_data.get("chart_type", "none")
        if chart_type == "none" or not visual_data.get("data_points"):
            return None

        colors = self._get_theme_colors(theme)
        title = visual_data.get("title", f"Slide {slide_num} Chart")
        x_label = visual_data.get("x_label", "")
        y_label = visual_data.get("y_label", "")
        data_points = visual_data.get("data_points", [])

        if not data_points:
            self.logger.warning(f"No data_points for slide {slide_num} chart; skipping.")
            return None

        try:
            dispatchers = {
                "bar": lambda: self.generate_bar_chart(data_points, title, x_label, y_label, colors, slide_num),
                "horizontal_bar": lambda: self.generate_bar_chart(data_points, title, x_label, y_label, colors, slide_num, horizontal=True),
                "line": lambda: self.generate_line_chart(data_points, title, x_label, y_label, colors, slide_num),
                "stacked_bar": lambda: self.generate_stacked_bar_chart(data_points, title, x_label, y_label, colors, slide_num),
                "pie": lambda: self.generate_pie_chart(data_points, title, colors, slide_num),
                "waterfall": lambda: self.generate_waterfall_chart(data_points, title, x_label, y_label, colors, slide_num),
                "funnel": lambda: self.generate_funnel_chart(data_points, title, colors, slide_num),
                "scatter": lambda: self.generate_scatter_chart(data_points, title, x_label, y_label, colors, slide_num),
            }
            fn = dispatchers.get(chart_type, dispatchers.get("bar"))
            chart_path = fn()
            self.logger.info(f"Chart saved: {chart_path}")
            return chart_path
        except Exception as e:
            self.logger.error(f"Chart generation failed for slide {slide_num} ({chart_type}): {e}", exc_info=True)
            return None

    def execute(self, state: dict) -> AgentResult:
        """
        Generate charts for all slides in the deck.

        State keys consumed: slide_contents, intent_spec
        State keys produced: chart_files
        """
        try:
            slide_contents = state.get("slide_contents", [])
            intent_spec = state.get("intent_spec", {})
            theme = intent_spec.get("recommended_theme", "default")
            chart_files = {}

            for slide in slide_contents:
                slide_num = slide.get("slide_number")
                visual_data = slide.get("visual_data")
                if visual_data and visual_data.get("chart_type") not in (None, "none"):
                    chart_path = self.generate_chart(slide_num, visual_data, theme)
                    if chart_path:
                        chart_files[slide_num] = {
                            "path": chart_path,
                            "chart_type": visual_data.get("chart_type"),
                            "title": visual_data.get("title", ""),
                        }

            self.logger.info(f"Generated {len(chart_files)} charts.")
            return AgentResult(
                success=True,
                data={"chart_files": chart_files},
                metadata={"chart_count": len(chart_files)},
            )
        except Exception as e:
            self.logger.error(f"ChartGeneratorAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
