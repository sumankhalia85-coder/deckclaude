# DeckClaude — AI-Powered Multi-Agent PowerPoint Generator

Transform any prompt, data file, or form input into a production-grade consulting presentation using a coordinated pipeline of specialized AI agents.

---

## Architecture

```
                          ┌─────────────────────────────────────────────┐
                          │            DeckClaude Pipeline               │
                          └─────────────────────────────────────────────┘

  User Input                     LangGraph Orchestrated Workflow
 ┌──────────┐   ┌─────────────────────────────────────────────────────────┐
 │  Prompt  │   │                                                         │
 │  Form    │──▶│  IntentAgent ──▶ [Research?] ──▶ BlueprintAgent         │
 │  File    │   │      │               │                  │               │
 └──────────┘   │      ▼               ▼                  ▼               │
                │   Intent Spec    Research         Slide Blueprint        │
                │                  Context          (SCQA + Pyramid)       │
                │                                         │               │
                │                                         ▼               │
                │                              InsightGeneratorAgent       │
                │                              (per-slide content)         │
                │                                         │               │
                │                    ┌────────────────────┤               │
                │                    ▼                    ▼               │
                │             VisualDesignAgent      [50/25/15/10]        │
                │                    │                                     │
                │       ┌────────────┼────────────┐                       │
                │       ▼            ▼            ▼                       │
                │  ChartAgent   SmartArt     ImageAgent                   │
                │  (matplotlib)  (pptx shapes)  (Unsplash/Pexels)         │
                │       │            │            │                       │
                │       └────────────┴────────────┘                       │
                │                    │                                     │
                │                    ▼                                     │
                │             DeckBuilderAgent                             │
                │             (python-pptx)                                │
                │                    │                                     │
                │                    ▼                                     │
                │             SlideCriticAgent ──▶ [Revise?] ──▶ Rebuild  │
                │                    │                                     │
                └────────────────────┼─────────────────────────────────────┘
                                     ▼
                            generated_presentation.pptx
```

---

## Setup

### 1. Clone and Install

```bash
cd C:/Users/Khalia/deckclaude
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
nano .env
```

### 3. Verify Setup

```bash
python cli.py status
```

---

## Usage

### Mode 1: Command-Line Prompt

```bash
python cli.py generate \
  --prompt "Quarterly AI adoption strategy for a Fortune 500 retail company" \
  --theme mckinsey \
  --slides 15
```

### Mode 2: With Data File

```bash
python cli.py generate \
  --file data/retail_sales_data.csv \
  --prompt "Analyze retail sales performance and recommend strategic actions" \
  --theme default \
  --slides 12
```

```bash
python cli.py generate \
  --file data/customer_churn_data.csv \
  --prompt "Customer churn analysis and retention strategy" \
  --theme consulting_green
```

### Mode 3: Interactive Form

```bash
python cli.py generate --form
```

Walks you through: deck type, audience, tone, slide count, theme.

### Mode 4: FastAPI (async generation)

```bash
# Start the API server
uvicorn app:app --reload --port 8000

# Trigger generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Q4 board presentation", "theme": "default", "slides": 12}'

# Check status
curl http://localhost:8000/status/{job_id}

# Download result
curl -O http://localhost:8000/download/Q4_board_presentation.pptx
```

### Mode 5: Upload file via API

```bash
curl -X POST http://localhost:8000/generate/upload \
  -F "file=@data/retail_sales_data.csv" \
  -F "prompt=Retail sales performance insights for exec team" \
  -F "theme=mckinsey" \
  -F "slides=10"
```

### Mode 6: Python API

```python
from workflows.deck_workflow import run_workflow

result = run_workflow({
    "prompt": "AI strategy for manufacturing sector",
    "requested_theme": "dark_tech",
    "requested_slides": 14,
    "file_path": "data/ai_adoption_trends.csv",
})

print(result["output_path"])
print(result["quality_report"]["overall_deck_score"])
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes* | — | Anthropic Claude API key |
| `OPENAI_API_KEY` | Yes* | — | OpenAI API key (*one of the two required) |
| `LLM_PROVIDER` | No | `anthropic` | `anthropic` or `openai` |
| `LLM_MODEL` | No | `claude-sonnet-4-6` | Model identifier |
| `UNSPLASH_ACCESS_KEY` | No | — | Unsplash API key for slide images |
| `PEXELS_API_KEY` | No | — | Pexels API key (fallback image source) |
| `OUTPUT_DIR` | No | `./output` | Directory for generated .pptx files |
| `ASSETS_DIR` | No | `./assets` | Directory for logos, image cache |

---

## Agent Descriptions

| Agent | File | Role |
|---|---|---|
| IntentAgent | `agents/intent_agent.py` | Classifies presentation type, audience, tone. Outputs structured intent spec. |
| ResearchDataAgent | `agents/research_agent.py` | Extracts text/stats from PDF, CSV, Excel, JSON files using PyMuPDF and pandas. |
| BlueprintAgent | `agents/blueprint_agent.py` | Generates SCQA-structured slide-by-slide blueprint using Pyramid Principle. |
| InsightGeneratorAgent | `agents/insight_agent.py` | Creates consulting-quality per-slide content with insight-driven headlines. |
| VisualDesignAgent | `agents/design_agent.py` | Plans visual type (50% chart / 25% diagram / 15% image / 10% text) and layout. |
| ChartGeneratorAgent | `agents/chart_agent.py` | Generates 7 chart types via matplotlib: bar, line, stacked_bar, pie, waterfall, funnel, scatter. |
| SmartArtAgent | `agents/smartart_agent.py` | Draws chevron, pyramid, circular, and timeline diagrams using native pptx shapes. |
| ImageIntelligenceAgent | `agents/image_agent.py` | Fetches Unsplash/Pexels images or generates matplotlib abstract visuals. |
| DeckBuilderAgent | `agents/deck_builder_agent.py` | Assembles final .pptx with brand theme, charts, tables, fonts, margins, slide numbers. |
| SlideCriticAgent | `agents/critic_agent.py` | Scores 6 quality dimensions per slide; revises weak headlines automatically. |

---

## Deck Types Supported

| Type | Slides | Use Case |
|---|---|---|
| `strategy_deck` | 15-20 | Corporate strategy, market entry, competitive positioning |
| `executive_update` | 8-12 | C-suite briefings, QBRs, board updates |
| `proposal_deck` | 12-18 | Sales proposals, RFP responses, partnership pitches |
| `training_deck` | 20-35 | Employee training, onboarding, skills development |
| `project_status` | 8-15 | Sprint reviews, milestone updates, risk dashboards |
| `research_summary` | 15-25 | Market research, competitive analysis, customer insights |
| `pitch_deck` | 10-15 | Investor pitches, fundraising decks |
| `board_presentation` | 12-20 | Governance reports, annual reviews, formal board meetings |

---

## Brand Themes

| Theme | Primary | Secondary | Accent | Best For |
|---|---|---|---|---|
| `default` | `#002060` (Navy) | `#00B0F0` (Blue) | `#FF6B35` (Orange) | General corporate |
| `mckinsey` | `#002F5F` (Dark Navy) | `#0070C0` (Blue) | `#D04A02` (Rust) | Consulting |
| `dark_tech` | `#1A1A2E` (Dark) | `#16213E` (Navy) | `#00D4FF` (Cyan) | Technology/SaaS |
| `consulting_green` | `#006B3C` (Forest) | `#00A651` (Green) | `#F7941D` (Amber) | Sustainability/ESG |

---

## Output Example

After generation:
```
output/
  Retail_AI_Strategy.pptx          ← Main presentation
  charts/
    slide_04_Market_Growth.png
    slide_07_Revenue_Waterfall.png
    slide_11_Channel_Mix.png
  images/
    abstract_slide_01.png
```

Each `.pptx` includes:
- Branded title slide with full-bleed visual
- Section dividers with theme accent colors
- Insight-driven headlines on every content slide
- Embedded charts (bar, line, waterfall, pie, etc.)
- SmartArt-style process flows and timelines
- Data callout boxes for key metrics
- Slide numbers and footer branding
- Speaker notes on every slide

---

## Quality Standards

The SlideCriticAgent scores every slide on 6 dimensions (0-10):
1. **Headline Quality** — Insight-driven vs. topic label
2. **Text Density** — Word count, bullet count
3. **Visual Balance** — Chart/diagram appropriateness
4. **Layout Compliance** — Margins, overflow, alignment
5. **Insight Strength** — Specificity, decision-enabling content
6. **Narrative Flow** — Logical connection to adjacent slides

A deck scores ≥7.5 average to be flagged "client-ready".

---

## Data Files Included

| File | Description |
|---|---|
| `data/retail_sales_data.csv` | 36-month retail performance by category (Electronics, Apparel, Home, Sports, Beauty) |
| `data/ai_adoption_trends.csv` | 2020-2026 AI adoption rates by industry and maturity level |
| `data/customer_churn_data.csv` | Churn analysis across 8 customer segments with NPS and LTV |
| `data/supply_chain_costs.csv` | 16-quarter supply chain cost breakdown by category with digitization index |
