"""
IntentAgent — Classifies user presentation requests into structured intent specifications.
Handles three input modes: free-text prompt, structured form data, and document content.
Outputs a validated intent JSON consumed by BlueprintAgent and downstream agents.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "strategy_deck", "executive_update", "proposal_deck", "training_deck",
    "project_status", "research_summary", "pitch_deck", "board_presentation",
}
VALID_TONES = {"formal", "semi-formal", "conversational", "technical", "inspirational"}
VALID_THEMES = {
    "default", "mckinsey", "dark_tech", "consulting_green",
    "bain", "bcg", "ey", "deloitte_black", "startup_minimal", "investor_pitch",
}
VALID_COMPLEXITY = {"simple", "moderate", "complex"}


class IntentAgent(BaseAgent):
    """
    Classifies a user's presentation request into a structured intent specification.

    Input state keys:
        prompt (str): Free-text description of the presentation (required if no form_data)
        form_data (dict, optional): Structured form fields (intent, audience, slides, etc.)
        document_text (str, optional): Extracted text from uploaded document for context
        requested_slides (int, optional): User-specified slide count override
        requested_theme (str, optional): User-specified theme override

    Output (AgentResult.data):
        {
          intent, audience, tone, slides, include_charts, include_diagrams,
          include_images, key_themes, deck_title, complexity_level,
          recommended_theme, data_requirements, primary_framework
        }
    """

    def __init__(self):
        super().__init__(
            name="IntentAgent",
            description="Classifies presentation requests into structured intent specifications",
        )
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "intent_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        logger.warning(f"Intent prompt not found at {prompt_path}, using built-in fallback.")
        return (
            "You are a presentation strategy expert. Analyze the user's request and return a "
            "JSON object with fields: intent, audience, tone, slides, include_charts, "
            "include_diagrams, include_images, key_themes, deck_title, complexity_level, "
            "recommended_theme, data_requirements, primary_framework."
        )

    def classify(
        self,
        prompt: Optional[str] = None,
        form_data: Optional[dict] = None,
        document_text: Optional[str] = None,
        requested_slides: Optional[int] = None,
        requested_theme: Optional[str] = None,
        requested_deck_type: Optional[str] = None,
    ) -> dict:
        """
        Core classification method. Constructs user message from available inputs,
        calls LLM, parses and validates the response.
        """
        user_message = self._build_user_message(
            prompt, form_data, document_text, requested_slides, requested_theme, requested_deck_type
        )
        raw_response = self.llm.complete(
            system_prompt=self._prompt_template,
            user_message=user_message,
            max_tokens=2048,
            temperature=0.2,
        )
        intent_data = self.parse_json(raw_response)
        return self._validate_and_default(intent_data, requested_slides, requested_theme, requested_deck_type)

    def _build_user_message(
        self,
        prompt: Optional[str],
        form_data: Optional[dict],
        document_text: Optional[str],
        requested_slides: Optional[int],
        requested_theme: Optional[str],
        requested_deck_type: Optional[str] = None,
    ) -> str:
        parts = []

        if prompt:
            parts.append(f"USER REQUEST:\n{prompt.strip()}")

        if form_data:
            parts.append("FORM DATA (pre-filled by user):")
            for k, v in form_data.items():
                parts.append(f"  {k}: {v}")

        if document_text:
            # Limit document context to avoid token overflow
            excerpt = document_text[:3000].strip()
            parts.append(f"UPLOADED DOCUMENT EXCERPT (use for context):\n{excerpt}")

        if requested_slides:
            parts.append(f"OVERRIDE: User explicitly requested {requested_slides} slides. Honor this count.")

        if requested_theme:
            parts.append(f"OVERRIDE: User requested theme '{requested_theme}'. Set recommended_theme to this value.")

        if requested_deck_type:
            parts.append(f"OVERRIDE: User explicitly selected deck type '{requested_deck_type}'. Set intent to this value exactly.")

        if not parts:
            parts.append("Create a general-purpose business presentation with 12 slides.")

        return "\n\n".join(parts)

    def _validate_and_default(
        self, data: dict, requested_slides: Optional[int], requested_theme: Optional[str],
        requested_deck_type: Optional[str] = None,
    ) -> dict:
        """Apply defaults and validate all fields, correcting invalid values."""

        # intent — honor explicit user deck type selection first
        if requested_deck_type and requested_deck_type in VALID_INTENTS:
            data["intent"] = requested_deck_type
        elif data.get("intent") not in VALID_INTENTS:
            logger.warning(f"Invalid intent '{data.get('intent')}', defaulting to 'strategy_deck'")
            data["intent"] = "strategy_deck"

        # audience
        if not data.get("audience") or not isinstance(data["audience"], str):
            data["audience"] = "Senior business executives and decision-makers"

        # tone
        if data.get("tone") not in VALID_TONES:
            data["tone"] = "semi-formal"

        # slides
        if requested_slides and isinstance(requested_slides, int):
            data["slides"] = max(4, min(50, requested_slides))
        elif not isinstance(data.get("slides"), int):
            data["slides"] = 12
        else:
            data["slides"] = max(4, min(50, data["slides"]))

        # boolean flags
        for flag in ("include_charts", "include_diagrams", "include_images"):
            if not isinstance(data.get(flag), bool):
                data[flag] = True

        # key_themes
        if not isinstance(data.get("key_themes"), list) or not data["key_themes"]:
            data["key_themes"] = ["business performance", "strategic growth", "operational excellence"]

        # deck_title
        if not data.get("deck_title") or not isinstance(data["deck_title"], str):
            data["deck_title"] = "Executive Presentation"

        # complexity_level
        if data.get("complexity_level") not in VALID_COMPLEXITY:
            data["complexity_level"] = "moderate"

        # recommended_theme
        if requested_theme and requested_theme.lower() in VALID_THEMES:
            data["recommended_theme"] = requested_theme.lower()
        elif data.get("recommended_theme") and data.get("recommended_theme").lower() in VALID_THEMES:
            data["recommended_theme"] = data["recommended_theme"].lower()
        else:
            data["recommended_theme"] = "default"

        # data_requirements
        if not isinstance(data.get("data_requirements"), list):
            data["data_requirements"] = []

        # primary_framework
        if not data.get("primary_framework") or not isinstance(data["primary_framework"], str):
            data["primary_framework"] = "SCQA"

        return data

    def execute(self, state: dict) -> AgentResult:
        """
        Execute intent classification from workflow state.

        State keys consumed: prompt, form_data, document_text,
                             requested_slides, requested_theme
        State keys produced: intent_spec
        """
        try:
            prompt = state.get("prompt", "")
            form_data = state.get("form_data")
            document_text = state.get("document_text")
            requested_slides = state.get("requested_slides")
            requested_theme = state.get("requested_theme")
            requested_deck_type = state.get("requested_deck_type")

            if not prompt and not form_data and not document_text:
                return AgentResult(
                    success=False,
                    data=None,
                    error="IntentAgent requires at least one of: prompt, form_data, document_text",
                )

            intent_spec = self.classify(
                prompt=prompt,
                form_data=form_data,
                document_text=document_text,
                requested_slides=requested_slides,
                requested_theme=requested_theme,
                requested_deck_type=requested_deck_type,
            )

            self.logger.info(
                f"Intent classified: {intent_spec['intent']} | "
                f"{intent_spec['slides']} slides | tone={intent_spec['tone']}"
            )

            return AgentResult(
                success=True,
                data={"intent_spec": intent_spec},
                metadata={
                    "intent": intent_spec["intent"],
                    "slides": intent_spec["slides"],
                    "theme": intent_spec["recommended_theme"],
                },
            )

        except Exception as e:
            self.logger.error(f"IntentAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
