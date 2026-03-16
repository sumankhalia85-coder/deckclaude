"""
DataSourceRouter — Matches prompt keywords to backend CSV datasets.
Runs before ResearchAgent in prompt-only mode; injects a file_path into state
so ResearchAgent processes real data instead of letting the LLM hallucinate numbers.

Also pre-computes chart_ready_data: aggregated data_points that InsightAgent
can embed directly into visual_data, bypassing LLM guesswork entirely.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---- Dataset catalogue ----

DATA_DIR = Path(__file__).parent.parent / "data"

DATASETS = {
    "retail_sales": {
        "file": DATA_DIR / "retail_sales_data.csv",
        "keywords": [
            "retail", "sales", "ecommerce", "e-commerce", "store", "consumer",
            "shopping", "revenue", "merchandise", "product", "units sold",
            "transaction", "purchase", "buyer", "market share",
        ],
        "description": "Retail sales performance by category, month, and year",
    },
    "ai_adoption": {
        "file": DATA_DIR / "ai_adoption_trends.csv",
        "keywords": [
            "ai", "artificial intelligence", "machine learning", "ml",
            "technology", "digital", "automation", "adoption", "tech",
            "innovation", "llm", "generative", "transformation", "data science",
            "intelligent", "algorithm",
        ],
        "description": "AI adoption rates, investment, and ROI across industries",
    },
    "customer_churn": {
        "file": DATA_DIR / "customer_churn_data.csv",
        "keywords": [
            "churn", "customer", "retention", "loyalty", "attrition",
            "lifetime value", "ltv", "clv", "nps", "satisfaction",
            "subscription", "cancel", "renewal", "engagement",
        ],
        "description": "Customer churn rates, LTV, and revenue risk by segment",
    },
    "supply_chain": {
        "file": DATA_DIR / "supply_chain_costs.csv",
        "keywords": [
            "supply chain", "logistics", "procurement", "warehouse",
            "cost", "supplier", "inventory", "manufacturing", "delivery",
            "lead time", "distribution", "sourcing", "operations",
            "efficiency", "fulfillment",
        ],
        "description": "Supply chain costs, efficiency scores, and disruption events",
    },
}


# ---- Aggregation helpers ----

def _safe_import_pandas():
    try:
        import pandas as pd
        return pd
    except ImportError:
        return None


def _build_retail_charts(df) -> dict:
    """Pre-compute chart data_points from retail_sales_data.csv."""
    charts = {}
    try:
        # Revenue by category (bar chart)
        if "category" in df.columns and "revenue_usd" in df.columns:
            cat_rev = df.groupby("category")["revenue_usd"].sum().sort_values(ascending=False)
            charts["category_revenue"] = {
                "chart_type": "bar",
                "title": "Revenue by Category",
                "x_label": "Category",
                "y_label": "Revenue (USD)",
                "data_points": [
                    {"label": str(k), "value": round(float(v) / 1_000_000, 2)}
                    for k, v in cat_rev.head(7).items()
                ],
                "unit": "USD Millions",
            }

        # Monthly revenue trend (line chart)
        if "month" in df.columns and "year" in df.columns and "revenue_usd" in df.columns:
            if "year" in df.columns:
                latest_year = df["year"].max()
                yr_df = df[df["year"] == latest_year]
            else:
                yr_df = df
            monthly = yr_df.groupby("month")["revenue_usd"].sum().reset_index()
            charts["monthly_trend"] = {
                "chart_type": "line",
                "title": f"Monthly Revenue Trend ({latest_year})",
                "x_label": "Month",
                "y_label": "Revenue (USD Millions)",
                "data_points": [
                    {"label": str(int(row["month"])), "value": round(float(row["revenue_usd"]) / 1_000_000, 2)}
                    for _, row in monthly.iterrows()
                ],
                "unit": "USD Millions",
            }

        # Online vs in-store mix (pie chart)
        if "online_pct" in df.columns:
            avg_online = round(float(df["online_pct"].mean()), 1)
            charts["channel_mix"] = {
                "chart_type": "pie",
                "title": "Sales Channel Mix",
                "data_points": [
                    {"label": "Online", "value": avg_online},
                    {"label": "In-Store", "value": round(100 - avg_online, 1)},
                ],
                "unit": "% of Sales",
            }

        # Customer satisfaction by category
        if "category" in df.columns and "customer_satisfaction_score" in df.columns:
            sat = df.groupby("category")["customer_satisfaction_score"].mean().sort_values(ascending=False)
            charts["satisfaction_by_category"] = {
                "chart_type": "horizontal_bar",
                "title": "Customer Satisfaction by Category",
                "x_label": "Satisfaction Score",
                "y_label": "Category",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 2)}
                    for k, v in sat.head(6).items()
                ],
                "unit": "Score (out of 10)",
            }

    except Exception as e:
        logger.warning(f"Retail chart aggregation error: {e}")

    return charts


def _build_ai_adoption_charts(df) -> dict:
    """Pre-compute chart data_points from ai_adoption_trends.csv."""
    charts = {}
    try:
        # Adoption rate by industry (bar chart)
        if "industry" in df.columns and "ai_adoption_rate_pct" in df.columns:
            ind_adopt = df.groupby("industry")["ai_adoption_rate_pct"].mean().sort_values(ascending=False)
            charts["adoption_by_industry"] = {
                "chart_type": "bar",
                "title": "AI Adoption Rate by Industry",
                "x_label": "Industry",
                "y_label": "Adoption Rate (%)",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in ind_adopt.head(8).items()
                ],
                "unit": "%",
            }

        # Investment trend over years (line chart)
        if "year" in df.columns and "investment_usd_millions" in df.columns:
            yr_invest = df.groupby("year")["investment_usd_millions"].sum()
            charts["investment_trend"] = {
                "chart_type": "line",
                "title": "AI Investment Trend by Year",
                "x_label": "Year",
                "y_label": "Investment (USD Millions)",
                "data_points": [
                    {"label": str(int(k)), "value": round(float(v), 1)}
                    for k, v in yr_invest.items()
                ],
                "unit": "USD Millions",
            }

        # ROI by industry (horizontal bar)
        if "industry" in df.columns and "roi_percentage" in df.columns:
            roi = df.groupby("industry")["roi_percentage"].mean().sort_values(ascending=False)
            charts["roi_by_industry"] = {
                "chart_type": "horizontal_bar",
                "title": "Average AI ROI by Industry",
                "x_label": "ROI (%)",
                "y_label": "Industry",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in roi.head(7).items()
                ],
                "unit": "%",
            }

        # Workforce impact over time (line chart)
        if "year" in df.columns and "workforce_impact_pct" in df.columns:
            wf = df.groupby("year")["workforce_impact_pct"].mean()
            charts["workforce_impact"] = {
                "chart_type": "line",
                "title": "Workforce Impact of AI Over Time",
                "x_label": "Year",
                "y_label": "Workforce Affected (%)",
                "data_points": [
                    {"label": str(int(k)), "value": round(float(v), 1)}
                    for k, v in wf.items()
                ],
                "unit": "%",
            }

    except Exception as e:
        logger.warning(f"AI adoption chart aggregation error: {e}")

    return charts


def _build_churn_charts(df) -> dict:
    """Pre-compute chart data_points from customer_churn_data.csv."""
    charts = {}
    try:
        # Churn rate by segment (bar chart)
        if "segment" in df.columns and "churn_rate_pct" in df.columns:
            churn = df.set_index("segment")["churn_rate_pct"].sort_values(ascending=False)
            charts["churn_by_segment"] = {
                "chart_type": "bar",
                "title": "Customer Churn Rate by Segment",
                "x_label": "Segment",
                "y_label": "Churn Rate (%)",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 2)}
                    for k, v in churn.items()
                ],
                "unit": "%",
            }

        # Revenue at risk by segment (horizontal bar)
        if "segment" in df.columns and "revenue_at_risk_usd_millions" in df.columns:
            rev = df.set_index("segment")["revenue_at_risk_usd_millions"].sort_values(ascending=False)
            charts["revenue_at_risk"] = {
                "chart_type": "horizontal_bar",
                "title": "Revenue at Risk by Segment",
                "x_label": "USD Millions",
                "y_label": "Segment",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in rev.items()
                ],
                "unit": "USD Millions",
            }

        # LTV by segment (bar chart)
        if "segment" in df.columns and "avg_lifetime_value_usd" in df.columns:
            ltv = df.set_index("segment")["avg_lifetime_value_usd"].sort_values(ascending=False)
            charts["ltv_by_segment"] = {
                "chart_type": "bar",
                "title": "Average Customer Lifetime Value by Segment",
                "x_label": "Segment",
                "y_label": "LTV (USD)",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 0)}
                    for k, v in ltv.items()
                ],
                "unit": "USD",
            }

        # NPS by segment
        if "segment" in df.columns and "nps_score" in df.columns:
            nps = df.set_index("segment")["nps_score"].sort_values(ascending=False)
            charts["nps_by_segment"] = {
                "chart_type": "bar",
                "title": "NPS Score by Customer Segment",
                "x_label": "Segment",
                "y_label": "NPS Score",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in nps.items()
                ],
                "unit": "NPS",
            }

    except Exception as e:
        logger.warning(f"Churn chart aggregation error: {e}")

    return charts


def _build_supply_chain_charts(df) -> dict:
    """Pre-compute chart data_points from supply_chain_costs.csv."""
    charts = {}
    try:
        # Cost by category (bar chart)
        if "category" in df.columns and "cost_usd_millions" in df.columns:
            cat_cost = df.groupby("category")["cost_usd_millions"].sum().sort_values(ascending=False)
            charts["cost_by_category"] = {
                "chart_type": "bar",
                "title": "Supply Chain Cost by Category",
                "x_label": "Category",
                "y_label": "Cost (USD Millions)",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in cat_cost.head(8).items()
                ],
                "unit": "USD Millions",
            }

        # Efficiency trend by year (line chart)
        if "year" in df.columns and "efficiency_score" in df.columns:
            eff = df.groupby("year")["efficiency_score"].mean()
            charts["efficiency_trend"] = {
                "chart_type": "line",
                "title": "Supply Chain Efficiency Trend",
                "x_label": "Year",
                "y_label": "Efficiency Score",
                "data_points": [
                    {"label": str(int(k)), "value": round(float(v), 2)}
                    for k, v in eff.items()
                ],
                "unit": "Score",
            }

        # Lead time by category
        if "category" in df.columns and "lead_time_days" in df.columns:
            lt = df.groupby("category")["lead_time_days"].mean().sort_values(ascending=False)
            charts["lead_time_by_category"] = {
                "chart_type": "horizontal_bar",
                "title": "Average Lead Time by Category",
                "x_label": "Days",
                "y_label": "Category",
                "data_points": [
                    {"label": str(k), "value": round(float(v), 1)}
                    for k, v in lt.head(7).items()
                ],
                "unit": "Days",
            }

        # Cost variance trend (line chart)
        if "year" in df.columns and "cost_variance_pct" in df.columns:
            cv = df.groupby("year")["cost_variance_pct"].mean()
            charts["cost_variance_trend"] = {
                "chart_type": "line",
                "title": "Cost Variance Trend Over Time",
                "x_label": "Year",
                "y_label": "Cost Variance (%)",
                "data_points": [
                    {"label": str(int(k)), "value": round(float(v), 2)}
                    for k, v in cv.items()
                ],
                "unit": "%",
            }

    except Exception as e:
        logger.warning(f"Supply chain chart aggregation error: {e}")

    return charts


_CHART_BUILDERS = {
    "retail_sales": _build_retail_charts,
    "ai_adoption": _build_ai_adoption_charts,
    "customer_churn": _build_churn_charts,
    "supply_chain": _build_supply_chain_charts,
}


# ---- Router logic ----

def _score_prompt(prompt: str, keywords: list) -> int:
    """Count keyword hits in the prompt (case-insensitive)."""
    prompt_lower = prompt.lower()
    return sum(1 for kw in keywords if kw in prompt_lower)


def match_dataset(prompt: str) -> Optional[str]:
    """Return the best matching dataset key for a given prompt, or None."""
    if not prompt:
        return None

    scores = {
        key: _score_prompt(prompt, cfg["keywords"])
        for key, cfg in DATASETS.items()
    }

    best_key = max(scores, key=lambda k: scores[k])
    best_score = scores[best_key]

    if best_score == 0:
        logger.info("DataSourceRouter: No keyword match — will use LLM knowledge only.")
        return None

    logger.info(f"DataSourceRouter: Matched '{best_key}' (score={best_score}) for prompt.")
    return best_key


def load_dataset(dataset_key: str):
    """Load the CSV for a dataset key; returns (DataFrame, file_path_str) or (None, None)."""
    pd = _safe_import_pandas()
    if pd is None:
        logger.warning("DataSourceRouter: pandas not installed — skipping CSV load.")
        return None, None

    cfg = DATASETS.get(dataset_key)
    if not cfg:
        return None, None

    file_path = cfg["file"]
    if not file_path.exists():
        logger.warning(f"DataSourceRouter: CSV not found at {file_path}")
        return None, None

    try:
        df = pd.read_csv(file_path)
        logger.info(f"DataSourceRouter: Loaded {dataset_key} — {len(df)} rows, {len(df.columns)} columns.")
        return df, str(file_path)
    except Exception as e:
        logger.warning(f"DataSourceRouter: Failed to load {file_path}: {e}")
        return None, None


def build_chart_ready_data(dataset_key: str, df) -> dict:
    """Build pre-computed chart data from a loaded DataFrame."""
    builder = _CHART_BUILDERS.get(dataset_key)
    if builder is None or df is None:
        return {}
    try:
        charts = builder(df)
        logger.info(f"DataSourceRouter: Built {len(charts)} chart datasets for '{dataset_key}'.")
        return charts
    except Exception as e:
        logger.warning(f"DataSourceRouter: Chart builder error for {dataset_key}: {e}")
        return {}


def route(prompt: str, existing_file_path: Optional[str] = None) -> dict:
    """
    Main entry point. Returns dict with:
      - file_path: str | None  (path to matched CSV, or existing file_path)
      - dataset_key: str | None
      - dataset_description: str | None
      - chart_ready_data: dict  (pre-aggregated chart data_points)
      - data_source: str  ("user_upload" | "backend_csv" | "none")
    """
    # If user already uploaded a file, don't override it
    if existing_file_path and Path(existing_file_path).exists():
        logger.info("DataSourceRouter: User-uploaded file present — skipping keyword routing.")
        return {
            "file_path": existing_file_path,
            "dataset_key": None,
            "dataset_description": None,
            "chart_ready_data": {},
            "data_source": "user_upload",
        }

    dataset_key = match_dataset(prompt)

    if dataset_key is None:
        return {
            "file_path": None,
            "dataset_key": None,
            "dataset_description": None,
            "chart_ready_data": {},
            "data_source": "none",
        }

    df, file_path = load_dataset(dataset_key)

    chart_ready_data = build_chart_ready_data(dataset_key, df) if df is not None else {}

    return {
        "file_path": file_path,
        "dataset_key": dataset_key,
        "dataset_description": DATASETS[dataset_key]["description"],
        "chart_ready_data": chart_ready_data,
        "data_source": "backend_csv" if file_path else "none",
    }
