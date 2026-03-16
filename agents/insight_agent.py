"""
InsightGeneratorAgent — Produces consulting-quality, SCQA-framed insights for each slide.
Takes the blueprint and research context as input; outputs per-slide content packages
with insight-driven headlines, supporting points, data callouts, and speaker notes.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class InsightGeneratorAgent(BaseAgent):
    """
    Generates slide-level content using the SCQA narrative framework.

    Input state keys:
        blueprint (dict): Output from BlueprintAgent
        research_context (dict, optional): Extracted file data
        research_summary (dict, optional): LLM summary of data
        intent_spec (dict): Intent specification for tone/audience context

    Output (AgentResult.data):
        {
          slide_contents: [
            {
              slide_number, headline, insights, supporting_points,
              data_callout, takeaway, speaker_notes, visual_data
            }
          ]
        }
    """

    def __init__(self):
        super().__init__(
            name="InsightGeneratorAgent",
            description="Generates SCQA-framed consulting insights per slide",
        )
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "insight_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "You are a senior management consultant. Generate actionable business insights "
            "for each slide. Every insight must be specific, quantified, and decision-enabling. "
            "Return valid JSON."
        )

    def _build_data_context(
        self,
        research_context: Optional[dict],
        research_summary: Optional[dict],
        chart_ready_data: Optional[dict] = None,
        dataset_description: Optional[str] = None,
    ) -> str:
        """Build a compact data context string for the LLM prompt."""
        parts = []

        if dataset_description:
            parts.append(f"DATA SOURCE: {dataset_description}")

        if chart_ready_data:
            parts.append("PRE-COMPUTED CHART DATA (use these exact values for data_points):")
            for chart_key, chart_info in list(chart_ready_data.items())[:4]:
                pts = chart_info.get("data_points", [])
                pts_str = ", ".join(
                    f"{p['label']}: {p['value']}{(' ' + chart_info.get('unit','')) if chart_info.get('unit') else ''}"
                    for p in pts[:6]
                )
                parts.append(f"  [{chart_key}] {chart_info.get('title', chart_key)} — {pts_str}")

        if research_summary:
            parts.append(f"RESEARCH OVERVIEW: {research_summary.get('overview', '')}")
            metrics = research_summary.get("key_metrics", [])
            if metrics:
                parts.append("KEY METRICS:")
                for m in metrics[:8]:
                    parts.append(f"  - {m.get('metric', '')}: {m.get('value', '')} — {m.get('interpretation', '')}")
            trends = research_summary.get("trends", [])
            if trends:
                parts.append("TRENDS: " + "; ".join(trends[:5]))

        if research_context and research_context.get("column_profiles"):
            profiles = research_context["column_profiles"]
            numeric_cols = [
                f"{col}: min={p.get('min','?')}, max={p.get('max','?')}, mean={p.get('mean','?')}"
                for col, p in profiles.items()
                if "mean" in p
            ]
            if numeric_cols:
                parts.append("NUMERIC COLUMNS: " + " | ".join(numeric_cols[:6]))

        return "\n".join(parts) if parts else "No data context provided."

    def _pick_chart_data(self, slide: dict, chart_ready_data: Optional[dict]) -> Optional[dict]:
        """
        Select the most relevant pre-computed chart dataset for a slide.
        Matches the slide's chart_type and key terms in its headline/data_needed.
        Returns a chart dict or None if no good match.
        """
        if not chart_ready_data:
            return None

        slide_chart_type = slide.get("chart_type", "").lower()
        text = (
            (slide.get("headline") or "") + " " +
            (slide.get("data_needed") or "") + " " +
            (slide.get("key_message") or "")
        ).lower()

        best_key = None
        best_score = 0

        for key, chart_info in chart_ready_data.items():
            score = 0
            # Prefer charts whose type matches the blueprint's chart_type
            if slide_chart_type and slide_chart_type != "none":
                if chart_info.get("chart_type", "") == slide_chart_type:
                    score += 3
                elif slide_chart_type in chart_info.get("chart_type", ""):
                    score += 1
            # Prefer charts whose title or key words overlap slide text
            chart_title = chart_info.get("title", "").lower()
            common_words = set(key.replace("_", " ").split()) & set(text.split())
            score += len(common_words)
            if any(word in chart_title for word in text.split() if len(word) > 4):
                score += 2

            if score > best_score:
                best_score = score
                best_key = key

        if best_key and best_score > 0:
            return chart_ready_data[best_key]
        # If no specific match but we have data, pick the first available
        return next(iter(chart_ready_data.values()), None)

    def generate_slide_content(
        self,
        slide: dict,
        intent_spec: dict,
        data_context: str,
        scqa: dict,
        chart_ready_data: Optional[dict] = None,
    ) -> dict:
        """Generate content for a single slide using the LLM."""
        slide_type = slide.get("slide_type", "content")

        # Title and section slides get minimal content
        if slide_type in ("title", "section"):
            return {
                "slide_number": slide["slide_number"],
                "headline": slide.get("headline", ""),
                "insights": [],
                "supporting_points": slide.get("supporting_points", []),
                "data_callout": None,
                "takeaway": slide.get("key_message", ""),
                "speaker_notes": slide.get("speaker_notes", ""),
                "visual_data": None,
            }

        user_message = f"""
SLIDE TO DEVELOP:
  Slide {slide['slide_number']}: {slide.get('headline', 'Untitled')}
  Type: {slide_type}
  Narrative Role: {slide.get('narrative_role', 'supporting_argument')}
  Key Message: {slide.get('key_message', '')}
  Current Supporting Points: {json.dumps(slide.get('supporting_points', []))}
  Visual Type: {slide.get('visual_type', 'none')}
  Chart Type: {slide.get('chart_type', 'none')}
  Data Needed: {slide.get('data_needed', '')}

PRESENTATION CONTEXT:
  Audience: {intent_spec.get('audience', 'Executives')}
  Tone: {intent_spec.get('tone', 'semi-formal')}
  Overall Story: {scqa.get('answer', '')}

DATA CONTEXT:
{data_context}

Generate a complete slide content package. Return JSON with these fields:
{{
  "headline": "Improved insight-driven headline (must contain a specific data point or clear implication)",
  "insights": ["top 3-5 specific insights for this slide"],
  "supporting_points": ["5 bullet points max, each under 15 words"],
  "data_callout": {{
    "primary_number": "most impactful single number",
    "unit": "unit of measurement",
    "context": "brief context (vs. what benchmark)",
    "visualization_suggestion": "how to visualize"
  }},
  "takeaway": "single sentence — the 'so what' of this slide",
  "speaker_notes": "what the presenter should say (2-4 sentences, adds depth beyond slide text)",
  "visual_data": {{
    "chart_type": "bar|line|pie|stacked_bar|waterfall|scatter|funnel|none",
    "data_points": [{{"label": "...", "value": ...}}],
    "x_label": "...",
    "y_label": "...",
    "title": "chart title"
  }}
}}
"""
        # Pick real chart data before calling LLM (so we can reference it in context)
        real_chart = self._pick_chart_data(slide, chart_ready_data)

        try:
            raw = self.llm.complete(
                system_prompt=self._system_prompt,
                user_message=user_message,
                max_tokens=2000,
                temperature=0.35,
            )
            content = self.parse_json(raw)
        except Exception as e:
            self.logger.warning(f"LLM failed for slide {slide['slide_number']}: {e}; using fallback.")
            content = self._fallback_content(slide)

        # Override LLM-generated data_points with real pre-computed values when available
        if real_chart and slide_type not in ("title", "section"):
            vd = content.get("visual_data") or {}
            vd["data_points"] = real_chart["data_points"]
            vd["chart_type"] = real_chart.get("chart_type", vd.get("chart_type", "bar"))
            if real_chart.get("x_label"):
                vd["x_label"] = real_chart["x_label"]
            if real_chart.get("y_label"):
                vd["y_label"] = real_chart["y_label"]
            if real_chart.get("title"):
                vd["title"] = real_chart["title"]
            content["visual_data"] = vd

        # Merge with slide metadata
        content["slide_number"] = slide["slide_number"]
        content["slide_type"] = slide_type
        content["narrative_role"] = slide.get("narrative_role", "supporting_argument")

        # Validate and clean
        content = self._validate_slide_content(content)
        return content

    def _validate_slide_content(self, content: dict) -> dict:
        """Ensure all required fields exist and meet quality constraints."""
        if not content.get("headline"):
            content["headline"] = f"Slide {content.get('slide_number', '?')}: Key Insight"

        if not isinstance(content.get("insights"), list):
            content["insights"] = []

        if not isinstance(content.get("supporting_points"), list):
            content["supporting_points"] = []

        # Enforce bullet limits
        content["supporting_points"] = content["supporting_points"][:5]

        # Truncate long bullets
        content["supporting_points"] = [
            bp[:120] if len(bp) > 120 else bp
            for bp in content["supporting_points"]
        ]

        if not content.get("takeaway"):
            content["takeaway"] = "Key strategic implication to be addressed."

        if not content.get("speaker_notes"):
            content["speaker_notes"] = content.get("takeaway", "")

        if not isinstance(content.get("data_callout"), dict):
            content["data_callout"] = None

        if not isinstance(content.get("visual_data"), dict):
            content["visual_data"] = None

        return content

    def _fallback_content(self, slide: dict) -> dict:
        """Minimal fallback content when LLM fails for a slide."""
        return {
            "headline": slide.get("headline", "Key Insight"),
            "insights": [slide.get("key_message", "Insight to be developed.")],
            "supporting_points": slide.get("supporting_points", [])[:5],
            "data_callout": None,
            "takeaway": slide.get("key_message", ""),
            "speaker_notes": slide.get("speaker_notes", ""),
            "visual_data": None,
        }

    def generate_all_slides(
        self,
        blueprint: dict,
        intent_spec: dict,
        research_context: Optional[dict],
        research_summary: Optional[dict],
        chart_ready_data: Optional[dict] = None,
        dataset_description: Optional[str] = None,
    ) -> list:
        """Generate content for all slides in the blueprint."""
        slides = blueprint.get("slides", [])
        scqa = blueprint.get("scqa", {})
        data_context = self._build_data_context(
            research_context, research_summary, chart_ready_data, dataset_description
        )

        slide_contents = []
        for slide in slides:
            self.logger.info(f"Generating insights for slide {slide.get('slide_number', '?')}...")
            content = self.generate_slide_content(
                slide, intent_spec, data_context, scqa, chart_ready_data=chart_ready_data
            )
            slide_contents.append(content)

        return slide_contents

    def execute(self, state: dict) -> AgentResult:
        """
        Execute insight generation from workflow state.

        State keys consumed: blueprint, intent_spec, research_context, research_summary,
                             chart_ready_data, dataset_description
        State keys produced: slide_contents
        """
        try:
            blueprint = state.get("blueprint")
            if not blueprint:
                return AgentResult(
                    success=False,
                    data=None,
                    error="InsightGeneratorAgent requires 'blueprint' in state.",
                )

            intent_spec = state.get("intent_spec", {})
            research_context = state.get("research_context")
            research_summary = state.get("research_summary")
            chart_ready_data = state.get("chart_ready_data") or {}
            dataset_description = state.get("dataset_description")

            if chart_ready_data:
                self.logger.info(
                    f"Using {len(chart_ready_data)} pre-computed chart datasets "
                    f"from backend CSV ({dataset_description or 'unknown'})."
                )

            slide_contents = self.generate_all_slides(
                blueprint, intent_spec, research_context, research_summary,
                chart_ready_data=chart_ready_data,
                dataset_description=dataset_description,
            )

            self.logger.info(f"Generated content for {len(slide_contents)} slides.")

            return AgentResult(
                success=True,
                data={"slide_contents": slide_contents},
                metadata={"slides_generated": len(slide_contents)},
            )

        except Exception as e:
            self.logger.error(f"InsightGeneratorAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
