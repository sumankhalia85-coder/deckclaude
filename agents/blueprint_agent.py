"""
BlueprintAgent — Generates a slide-by-slide structural blueprint for the presentation.
Takes the intent specification and produces a complete narrative blueprint using
the SCQA framework and deck_types.json structure templates as a starting point.
The LLM customizes the blueprint to match the specific request and data context.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class BlueprintAgent(BaseAgent):
    """
    Generates a detailed slide-by-slide blueprint from an intent specification.

    Input state keys:
        intent_spec (dict): Output from IntentAgent
        research_summary (dict, optional): High-level summary of uploaded data

    Output (AgentResult.data):
        {
          blueprint: {
            deck_title, governing_question, scqa, storyline_arc,
            slides: [{slide_number, slide_type, headline, narrative_role,
                      key_message, supporting_points, data_needed,
                      visual_type, chart_type, speaker_notes, transition_to_next}],
            appendix_slides: [...]
          }
        }
    """

    def __init__(self):
        super().__init__(
            name="BlueprintAgent",
            description="Generates slide-by-slide narrative blueprints using SCQA and Pyramid Principle",
        )
        self._system_prompt = self._load_system_prompt()
        self._deck_types = self._load_deck_types()

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "storyline_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        logger.warning("Storyline prompt not found; using minimal fallback.")
        return (
            "You are a McKinsey consultant. Generate a complete slide-by-slide presentation "
            "blueprint using the SCQA framework. Return valid JSON with 'slides' array. "
            "Every headline must be an insight, not a topic label."
        )

    def _load_deck_types(self) -> dict:
        types_path = Path(__file__).parent.parent / "config" / "deck_types.json"
        if types_path.exists():
            with open(types_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("deck_types", {})
        logger.warning("deck_types.json not found; template structures unavailable.")
        return {}

    def _get_template_structure(self, intent: str) -> str:
        """Return the template slide structure for the given deck type as formatted text."""
        template = self._deck_types.get(intent)
        if not template:
            return "No specific template found. Use best judgment for slide structure."
        slides_desc = []
        for s in template.get("slides", []):
            slides_desc.append(
                f"  Slide {s['slide_number']}: [{s['slide_type'].upper()}] {s['title']} "
                f"(content_type: {s['content_type']}, layout: {s['layout']})"
            )
        return (
            f"Template: {template['name']}\n"
            f"Typical slide count: {template['typical_slide_count']}\n"
            f"Description: {template['description']}\n\n"
            f"Reference slide structure:\n" + "\n".join(slides_desc)
        )

    def generate_blueprint(self, intent_spec: dict, research_summary: Optional[dict] = None) -> dict:
        """
        Call LLM to generate a full narrative blueprint customized to the request.
        Falls back to a structured default if LLM fails.
        """
        intent = intent_spec.get("intent", "strategy_deck")
        template_text = self._get_template_structure(intent)
        slide_count = intent_spec.get("slides", 12)

        user_message_parts = [
            f"PRESENTATION REQUEST:",
            f"  Title: {intent_spec.get('deck_title', 'Executive Presentation')}",
            f"  Intent: {intent}",
            f"  Audience: {intent_spec.get('audience', 'Executives')}",
            f"  Tone: {intent_spec.get('tone', 'semi-formal')}",
            f"  Slide count: {slide_count}",
            f"  Key themes: {', '.join(intent_spec.get('key_themes', []))}",
            f"  Include charts: {intent_spec.get('include_charts', True)}",
            f"  Include diagrams: {intent_spec.get('include_diagrams', True)}",
            f"  Primary framework: {intent_spec.get('primary_framework', 'SCQA')}",
            "",
            f"REFERENCE TEMPLATE:\n{template_text}",
        ]

        if research_summary:
            data_ctx = json.dumps(research_summary, indent=2)[:2000]
            user_message_parts.append(f"\nDATA CONTEXT (shape your storyline around this):\n{data_ctx}")

        user_message_parts.append(
            f"\nGenerate a complete {slide_count}-slide blueprint. "
            f"Every headline must contain a specific insight. "
            f"Return only valid JSON matching the specified output structure."
        )

        user_message = "\n".join(user_message_parts)

        raw_response = self.llm.complete(
            system_prompt=self._system_prompt,
            user_message=user_message,
            max_tokens=6000,
            temperature=0.3,
        )

        blueprint = self.parse_json(raw_response)
        return self._validate_blueprint(blueprint, intent_spec)

    def _validate_blueprint(self, blueprint: dict, intent_spec: dict) -> dict:
        """Ensure required fields exist and slides are properly structured."""

        # Top-level required fields
        if not blueprint.get("deck_title"):
            blueprint["deck_title"] = intent_spec.get("deck_title", "Executive Presentation")

        if not blueprint.get("governing_question"):
            blueprint["governing_question"] = f"How should we address {', '.join(intent_spec.get('key_themes', ['the business challenge']))}?"

        if not isinstance(blueprint.get("scqa"), dict):
            blueprint["scqa"] = {
                "situation": "The business faces strategic challenges requiring immediate attention.",
                "complication": "Current approaches are insufficient to achieve desired outcomes.",
                "question": "What actions must we take to improve performance?",
                "answer": "A targeted three-part strategy addresses the root causes.",
            }

        if not blueprint.get("storyline_arc"):
            blueprint["storyline_arc"] = "Problem to solution narrative with evidence-based recommendations."

        # Validate slides array
        slides = blueprint.get("slides", [])
        if not isinstance(slides, list) or len(slides) == 0:
            blueprint["slides"] = self._generate_fallback_slides(intent_spec)
            slides = blueprint["slides"]

        required_slide_keys = {
            "slide_number", "slide_type", "headline", "narrative_role",
            "key_message", "supporting_points", "data_needed",
            "visual_type", "chart_type", "speaker_notes", "transition_to_next",
        }
        valid_slide_types = {"title", "section", "content", "chart", "two_column", "table", "diagram", "image_content", "thank_you"}
        valid_visual_types = {"none", "chart", "diagram", "table", "image", "icon_grid"}
        valid_chart_types = {"bar", "line", "stacked_bar", "pie", "waterfall", "scatter", "funnel", "none"}

        for i, slide in enumerate(slides):
            # Ensure all keys exist
            for key in required_slide_keys:
                if key not in slide:
                    slide[key] = self._default_slide_value(key, i + 1)

            # Normalize types
            if slide["slide_type"] not in valid_slide_types:
                slide["slide_type"] = "content"
            if slide["visual_type"] not in valid_visual_types:
                slide["visual_type"] = "none"
            if slide["chart_type"] not in valid_chart_types:
                slide["chart_type"] = "none"

            # Ensure supporting_points is a list
            if not isinstance(slide.get("supporting_points"), list):
                slide["supporting_points"] = []

            # Enforce slide numbering
            slide["slide_number"] = i + 1

        if not isinstance(blueprint.get("appendix_slides"), list):
            blueprint["appendix_slides"] = []

        return blueprint

    def _default_slide_value(self, key: str, slide_number: int):
        defaults = {
            "slide_number": slide_number,
            "slide_type": "content",
            "headline": f"Slide {slide_number}: Key Insights",
            "narrative_role": "supporting_argument",
            "key_message": "Key insight to be developed.",
            "supporting_points": [],
            "data_needed": "Supporting data and analysis",
            "visual_type": "none",
            "chart_type": "none",
            "speaker_notes": "",
            "transition_to_next": "",
        }
        return defaults.get(key, "")

    def _generate_fallback_slides(self, intent_spec: dict) -> list:
        """Generate a minimal valid slide structure if LLM response is unusable."""
        templates = self._deck_types.get(intent_spec.get("intent", "strategy_deck"), {})
        template_slides = templates.get("slides", [])
        slide_count = intent_spec.get("slides", 10)

        fallback = []
        for i in range(min(slide_count, max(len(template_slides), slide_count))):
            if i < len(template_slides):
                t = template_slides[i]
                fallback.append({
                    "slide_number": i + 1,
                    "slide_type": t.get("slide_type", "content"),
                    "headline": t.get("title", f"Slide {i + 1}"),
                    "narrative_role": "supporting_argument",
                    "key_message": "Insight to be generated.",
                    "supporting_points": [],
                    "data_needed": t.get("content_type", ""),
                    "visual_type": "none",
                    "chart_type": "none",
                    "speaker_notes": "",
                    "transition_to_next": "",
                })
            else:
                fallback.append({
                    "slide_number": i + 1,
                    "slide_type": "content",
                    "headline": f"Additional Analysis — Slide {i + 1}",
                    "narrative_role": "supporting_argument",
                    "key_message": "Supporting analysis.",
                    "supporting_points": [],
                    "data_needed": "",
                    "visual_type": "none",
                    "chart_type": "none",
                    "speaker_notes": "",
                    "transition_to_next": "",
                })
        return fallback

    def execute(self, state: dict) -> AgentResult:
        """
        Execute blueprint generation from workflow state.

        State keys consumed: intent_spec, research_summary (optional)
        State keys produced: blueprint
        """
        try:
            intent_spec = state.get("intent_spec")
            if not intent_spec:
                return AgentResult(
                    success=False,
                    data=None,
                    error="BlueprintAgent requires 'intent_spec' in state (run IntentAgent first).",
                )

            research_summary = state.get("research_summary")
            blueprint = self.generate_blueprint(intent_spec, research_summary)

            slide_count = len(blueprint.get("slides", []))
            self.logger.info(
                f"Blueprint generated: '{blueprint.get('deck_title')}' | {slide_count} slides"
            )

            return AgentResult(
                success=True,
                data={"blueprint": blueprint},
                metadata={
                    "slide_count": slide_count,
                    "deck_title": blueprint.get("deck_title"),
                    "intent": intent_spec.get("intent"),
                },
            )

        except Exception as e:
            self.logger.error(f"BlueprintAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
