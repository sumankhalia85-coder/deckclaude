"""
VisualDesignAgent — Decides visual type and layout for each slide using the
50/25/15/10 distribution rule: 50% chart, 25% diagram, 15% image, 10% text-only.
Coordinates which visual agents are called and defines the visual plan per slide.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

# Visual type distribution targets (percentage of content slides)
VISUAL_DISTRIBUTION = {
    "chart": 0.40,
    "diagram": 0.25,
    "image": 0.25,
    "text_only": 0.10,
}

# Layout options and their descriptions
LAYOUT_OPTIONS = {
    "full_bleed": "Visual fills the full slide width, text overlay at bottom",
    "split_left": "Text on left ~40%, visual on right ~60%",
    "split_right": "Visual on left ~60%, text on right ~40%",
    "header_content": "Headline at top, content/visual below",
    "two_column": "Two equal content columns side by side",
    "visual_dominant": "Visual takes 75% of slide, text callout only",
}

# Chart type assignments by narrative role
ROLE_TO_CHART = {
    "situation": "bar",
    "complication": "line",
    "evidence": "stacked_bar",
    "supporting_argument": "bar",
    "recommendation": "waterfall",
    "call_to_action": "funnel",
    "implication": "scatter",
    "hook": "pie",
}

# Diagram assignments by content description keywords
DIAGRAM_KEYWORDS = {
    "process": "chevron",
    "step": "chevron",
    "flow": "chevron",
    "stage": "chevron",
    "phase": "roadmap",
    "timeline": "roadmap",
    "roadmap": "roadmap",
    "milestone": "roadmap",
    "pyramid": "pyramid",
    "priority": "pyramid",
    "hierarchy": "pyramid",
    "strategy": "pyramid",
    "cycle": "circular",
    "circular": "circular",
    "loop": "circular",
    "framework": "chevron",
}


class VisualDesignAgent(BaseAgent):
    """
    Plans the visual design for each slide in the deck.
    Decides: visual_type, chart_type, layout, and which supporting agents to call.

    Input state keys:
        blueprint (dict): Slide blueprint from BlueprintAgent
        slide_contents (list): Content packages from InsightGeneratorAgent
        intent_spec (dict): For theme and preference context

    Output (AgentResult.data):
        {
          visual_plan: [
            {
              slide_number, visual_type, chart_type, diagram_type, layout,
              needs_chart_agent, needs_smartart_agent, needs_image_agent,
              image_style, notes
            }
          ],
          diagram_requests: [{slide_number, diagram_type, items, title}]
        }
    """

    def __init__(self):
        super().__init__(
            name="VisualDesignAgent",
            description="Plans visual type and layout for each slide using the 50/25/15/10 rule",
        )

    def _detect_diagram_type(self, slide_content: dict, blueprint_slide: dict) -> Optional[str]:
        """Detect the best diagram type from slide content and blueprint metadata."""
        # Check data_needed and content_type fields
        search_text = " ".join([
            blueprint_slide.get("data_needed", ""),
            blueprint_slide.get("content_type", ""),
            slide_content.get("takeaway", ""),
            " ".join(slide_content.get("supporting_points", [])),
        ]).lower()

        for keyword, diagram_type in DIAGRAM_KEYWORDS.items():
            if keyword in search_text:
                return diagram_type

        # Check blueprint visual_type
        visual_type = blueprint_slide.get("visual_type", "")
        if visual_type == "diagram":
            return "chevron"  # default diagram type

        return None

    def _determine_layout(
        self, visual_type: str, slide_type: str, has_chart: bool, has_diagram: bool
    ) -> str:
        """Select the most appropriate slide layout based on visual type."""
        if slide_type == "title":
            return "full_bleed"
        if slide_type == "section":
            return "header_content"
        if visual_type == "chart":
            return "header_content"  # headline at top, chart below
        if visual_type == "diagram":
            return "header_content"
        if visual_type == "image":
            return "split_right" if slide_type == "content" else "full_bleed"
        if visual_type == "table":
            return "header_content"
        # two_column slides
        if slide_type == "two_column":
            return "two_column"
        return "header_content"

    def plan_visuals(self, blueprint: dict, slide_contents: list, intent_spec: dict) -> tuple:
        """
        Produce a visual plan for every slide.
        Returns (visual_plan list, diagram_requests list).
        """
        slides = blueprint.get("slides", [])
        include_charts = intent_spec.get("include_charts", True)
        include_diagrams = intent_spec.get("include_diagrams", True)
        include_images = intent_spec.get("include_images", True)

        # Build a lookup for blueprint slides by number
        bp_by_num = {s["slide_number"]: s for s in slides}
        # Build a lookup for content by slide number
        content_by_num = {c["slide_number"]: c for c in slide_contents}

        # Determine how many content slides (exclude title/section)
        content_slides = [s for s in slides if s.get("slide_type") not in ("title", "section")]
        total_content = len(content_slides)

        # Allocate visual budget
        chart_budget = max(1, int(total_content * VISUAL_DISTRIBUTION["chart"]))
        diagram_budget = max(1, int(total_content * VISUAL_DISTRIBUTION["diagram"])) if include_diagrams else 0
        image_budget = max(1, int(total_content * VISUAL_DISTRIBUTION["image"])) if include_images else 0

        chart_count = 0
        diagram_count = 0
        image_count = 0

        visual_plan = []
        diagram_requests = []

        for slide in slides:
            snum = slide["slide_number"]
            stype = slide.get("slide_type", "content")
            narrative_role = slide.get("narrative_role", "supporting_argument")
            blueprint_visual_type = slide.get("visual_type", "none")
            blueprint_chart_type = slide.get("chart_type", "none")

            content = content_by_num.get(snum, {})
            visual_data = content.get("visual_data") or {}

            plan_entry = {
                "slide_number": snum,
                "slide_type": stype,
                "visual_type": "none",
                "chart_type": "none",
                "diagram_type": None,
                "layout": "header_content",
                "needs_chart_agent": False,
                "needs_smartart_agent": False,
                "needs_image_agent": False,
                "image_style": "abstract",
                "notes": "",
            }

            # Title slides always get an image
            if stype == "title":
                plan_entry["visual_type"] = "image"
                plan_entry["layout"] = "full_bleed"
                plan_entry["needs_image_agent"] = True
                plan_entry["image_style"] = "abstract"

            elif stype == "section":
                plan_entry["visual_type"] = "none"
                plan_entry["layout"] = "header_content"

            else:
                # Determine best visual from: blueprint signal, content data, budget
                decided = False

                # 1. If blueprint explicitly says chart and there's chart data
                if (blueprint_visual_type == "chart" or blueprint_chart_type not in ("none", ""))\
                        and include_charts and chart_count < chart_budget:
                    chart_type = visual_data.get("chart_type") or blueprint_chart_type or \
                                 ROLE_TO_CHART.get(narrative_role, "bar")
                    if chart_type not in ("none", ""):
                        plan_entry["visual_type"] = "chart"
                        plan_entry["chart_type"] = chart_type
                        plan_entry["needs_chart_agent"] = True
                        chart_count += 1
                        decided = True

                # 2. If blueprint says diagram
                if not decided and blueprint_visual_type == "diagram" and include_diagrams and diagram_count < diagram_budget:
                    diagram_type = self._detect_diagram_type(content, slide)
                    if diagram_type:
                        plan_entry["visual_type"] = "diagram"
                        plan_entry["diagram_type"] = diagram_type
                        plan_entry["needs_smartart_agent"] = True
                        diagram_count += 1
                        decided = True

                        # Prepare diagram request
                        items = [
                            pt.split(":")[-1].strip() if ":" in pt else pt
                            for pt in content.get("supporting_points", [])[:6]
                        ]
                        if not items:
                            items = [f"Step {i+1}" for i in range(4)]
                        diagram_requests.append({
                            "slide_number": snum,
                            "diagram_type": diagram_type,
                            "items": items,
                            "title": content.get("headline", slide.get("headline", "")),
                            "content_type": blueprint_visual_type,
                        })

                # 3. Insight-generated chart data
                if not decided and visual_data.get("chart_type") not in (None, "none") \
                        and include_charts and chart_count < chart_budget * 1.5:
                    plan_entry["visual_type"] = "chart"
                    plan_entry["chart_type"] = visual_data["chart_type"]
                    plan_entry["needs_chart_agent"] = True
                    chart_count += 1
                    decided = True

                # 4. Assign image if budget remains
                if not decided and include_images and image_count < image_budget:
                    plan_entry["visual_type"] = "image"
                    plan_entry["needs_image_agent"] = True
                    plan_entry["layout"] = "two_column"
                    plan_entry["image_style"] = "abstract"
                    image_count += 1
                    decided = True

                # 5. Fall back to text-only
                if not decided:
                    plan_entry["visual_type"] = "text_only"

                plan_entry["layout"] = self._determine_layout(
                    plan_entry["visual_type"], stype,
                    plan_entry["needs_chart_agent"], plan_entry["needs_smartart_agent"]
                )

            visual_plan.append(plan_entry)

        return visual_plan, diagram_requests

    def execute(self, state: dict) -> AgentResult:
        """
        Plan visuals for all slides.

        State keys consumed: blueprint, slide_contents, intent_spec
        State keys produced: visual_plan, diagram_requests
        """
        try:
            blueprint = state.get("blueprint")
            if not blueprint:
                return AgentResult(
                    success=False,
                    data=None,
                    error="VisualDesignAgent requires 'blueprint' in state.",
                )

            slide_contents = state.get("slide_contents", [])
            intent_spec = state.get("intent_spec", {})

            visual_plan, diagram_requests = self.plan_visuals(blueprint, slide_contents, intent_spec)

            chart_count = sum(1 for p in visual_plan if p["needs_chart_agent"])
            diagram_count = sum(1 for p in visual_plan if p["needs_smartart_agent"])
            image_count = sum(1 for p in visual_plan if p["needs_image_agent"])

            self.logger.info(
                f"Visual plan complete: {len(visual_plan)} slides | "
                f"{chart_count} charts | {diagram_count} diagrams | {image_count} images"
            )

            return AgentResult(
                success=True,
                data={
                    "visual_plan": visual_plan,
                    "diagram_requests": diagram_requests,
                },
                metadata={
                    "total_slides": len(visual_plan),
                    "chart_count": chart_count,
                    "diagram_count": diagram_count,
                    "image_count": image_count,
                },
            )

        except Exception as e:
            self.logger.error(f"VisualDesignAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
