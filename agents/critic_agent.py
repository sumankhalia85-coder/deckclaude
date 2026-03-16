"""
SlideCriticAgent — Reviews presentations against consulting quality standards.
Scores each slide on 6 dimensions, generates specific revision suggestions,
and produces an overall quality report. Can trigger slide content regeneration
for slides that fail the quality bar.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

PASS_THRESHOLD = 7.0  # Minimum score for a slide to be approved


class SlideCriticAgent(BaseAgent):
    """
    Reviews presentation quality against consulting standards.

    Input state keys:
        slide_contents (list): Per-slide content packages
        blueprint (dict): Structural blueprint for context
        intent_spec (dict): For audience/tone context

    Output (AgentResult.data):
        {
          quality_report: {
            overall_deck_score, overall_assessment, ready_for_client,
            critical_issues, slide_reviews, deck_level_issues,
            strengths, revision_priority, estimated_revision_effort
          },
          slides_requiring_revision: [slide_numbers],
          approved_slides: [slide_numbers]
        }
    """

    def __init__(self):
        super().__init__(
            name="SlideCriticAgent",
            description="Reviews slides against consulting quality standards; scores 6 dimensions",
        )
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "critic_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "You are a senior consultant reviewing a presentation. Score each slide 0-10 on: "
            "headline_quality, text_density, visual_balance, layout_compliance, "
            "insight_strength, narrative_flow. Return structured JSON quality report."
        )

    def _count_words(self, slide_content: dict) -> int:
        """Count total words on a slide (headline + bullets + takeaway)."""
        text_parts = [
            slide_content.get("headline", ""),
            slide_content.get("takeaway", ""),
        ] + slide_content.get("supporting_points", [])
        return sum(len(t.split()) for t in text_parts)

    def _check_headline_quality(self, headline: str) -> tuple:
        """
        Quick rule-based headline quality check.
        Returns (score 0-10, list of issues).
        """
        issues = []
        score = 10.0

        if not headline or not headline.strip():
            return 0.0, ["Headline is missing"]

        bad_endings = ["overview", "summary", "update", "analysis", "review", "introduction",
                       "background", "context", "conclusion", "next steps", "agenda"]
        h_lower = headline.lower().strip()
        for bad in bad_endings:
            if h_lower.endswith(bad) or h_lower == bad:
                issues.append(f"Headline ends with generic word: '{bad}'")
                score -= 4.0
                break

        if len(headline.split()) < 4:
            issues.append("Headline too short to convey an insight")
            score -= 2.0

        if len(headline.split()) > 20:
            issues.append("Headline too long (>20 words)")
            score -= 1.0

        # Check for numbers (good) — data-driven headlines
        import re
        has_number = bool(re.search(r"\d+", headline))
        if not has_number:
            issues.append("Headline contains no specific data point or number")
            score -= 2.0

        # Check for vague words
        vague_words = ["various", "several", "many", "some", "things", "aspects", "factors", "issues"]
        for vw in vague_words:
            if f" {vw} " in f" {h_lower} ":
                issues.append(f"Vague word in headline: '{vw}'")
                score -= 1.0
                break

        return max(0.0, min(10.0, score)), issues

    def _check_text_density(self, slide_content: dict) -> tuple:
        """Check text density; return (score, issues)."""
        issues = []
        score = 10.0

        slide_type = slide_content.get("slide_type", "content")
        if slide_type in ("title", "section"):
            return 10.0, []

        word_count = self._count_words(slide_content)
        bullets = slide_content.get("supporting_points", [])
        n_bullets = len(bullets)
        long_bullets = [b for b in bullets if len(b.split()) > 20]

        if word_count > 150:
            issues.append(f"Total word count {word_count} exceeds 150-word limit")
            score -= 4.0
        elif word_count > 100:
            issues.append(f"Total word count {word_count} is high (target <80)")
            score -= 2.0

        if n_bullets > 5:
            issues.append(f"{n_bullets} bullets on slide (max 5)")
            score -= 2.5
        elif n_bullets > 4:
            issues.append(f"{n_bullets} bullets (target ≤4 for senior audiences)")
            score -= 1.0

        if long_bullets:
            issues.append(f"{len(long_bullets)} bullet(s) exceed 20 words")
            score -= 1.5

        return max(0.0, min(10.0, score)), issues

    def review_slide_locally(self, slide_content: dict) -> dict:
        """
        Fast rule-based review for a single slide.
        Returns a partial review dict (LLM will fill in the rest).
        """
        headline = slide_content.get("headline", "")
        slide_num = slide_content.get("slide_number", 0)

        hl_score, hl_issues = self._check_headline_quality(headline)
        td_score, td_issues = self._check_text_density(slide_content)

        all_issues = hl_issues + td_issues
        slide_score = round((hl_score + td_score + 8.0 + 8.0 + 7.0 + 7.5) / 6, 2)

        return {
            "slide_number": slide_num,
            "slide_title": headline,
            "local_scores": {
                "headline_quality": hl_score,
                "text_density": td_score,
            },
            "local_issues": all_issues,
            "pre_screen_passed": hl_score >= 5.0 and td_score >= 5.0,
        }

    def review_deck_with_llm(self, slide_contents: list, blueprint: dict, intent_spec: dict) -> dict:
        """Call LLM for a comprehensive deck quality review."""
        # Build a compact representation of the deck
        deck_repr = []
        for sc in slide_contents:
            deck_repr.append({
                "slide_number": sc.get("slide_number"),
                "slide_type": sc.get("slide_type"),
                "headline": sc.get("headline", ""),
                "supporting_points": sc.get("supporting_points", []),
                "takeaway": sc.get("takeaway", ""),
                "has_chart": sc.get("visual_data") is not None,
                "word_count": self._count_words(sc),
            })

        user_message = f"""
Review this {len(slide_contents)}-slide {intent_spec.get('intent', 'business')} presentation
for a {intent_spec.get('audience', 'executive')} audience.

DECK CONTENT:
{json.dumps(deck_repr, indent=2)[:8000]}

GOVERNING QUESTION: {blueprint.get('governing_question', 'N/A')}
STORYLINE ARC: {blueprint.get('storyline_arc', 'N/A')}

Evaluate ALL slides and return a complete quality_report JSON.
Be specific and critical — consulting partner standards apply.
"""
        try:
            raw = self.llm.complete(
                system_prompt=self._system_prompt,
                user_message=user_message,
                max_tokens=6000,
                temperature=0.2,
            )
            report = self.parse_json(raw)
            return self._validate_quality_report(report, slide_contents)
        except Exception as e:
            self.logger.warning(f"LLM quality review failed: {e}; using rule-based fallback.")
            return self._rule_based_report(slide_contents, intent_spec)

    def _rule_based_report(self, slide_contents: list, intent_spec: dict) -> dict:
        """Generate a quality report using only rule-based checks (no LLM)."""
        slide_reviews = []
        for sc in slide_contents:
            pre = self.review_slide_locally(sc)
            hl_score = pre["local_scores"]["headline_quality"]
            td_score = pre["local_scores"]["text_density"]
            slide_score = round((hl_score + td_score + 7.5 + 8.0 + 6.5 + 7.0) / 6, 2)

            slide_reviews.append({
                "slide_number": sc.get("slide_number"),
                "slide_title": sc.get("headline", ""),
                "scores": {
                    "headline_quality": hl_score,
                    "text_density": td_score,
                    "visual_balance": 7.5,
                    "layout_compliance": 8.0,
                    "insight_strength": 6.5,
                    "narrative_flow": 7.0,
                },
                "slide_score": slide_score,
                "flags": pre["local_issues"],
                "revision_suggestions": [
                    {"dimension": "headline_quality", "issue": issue,
                     "suggestion": "Revise to include specific data point and clear implication.",
                     "priority": "must_fix"}
                    for issue in pre["local_issues"] if "headline" in issue.lower()
                ],
                "revised_headline_suggestion": None,
                "approved": slide_score >= PASS_THRESHOLD,
            })

        scores = [r["slide_score"] for r in slide_reviews]
        overall = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "overall_deck_score": overall,
            "overall_assessment": f"Rule-based review: {len(slide_reviews)} slides assessed. "
                                   f"Average score {overall:.1f}/10.",
            "ready_for_client": overall >= 7.5,
            "critical_issues": [
                r["slide_title"] + ": " + "; ".join(r["flags"])
                for r in slide_reviews if not r["approved"] and r["flags"]
            ],
            "slide_reviews": slide_reviews,
            "deck_level_issues": [],
            "strengths": ["Presentation structure follows recommended template"],
            "revision_priority": [r["slide_title"] for r in slide_reviews if not r["approved"]][:5],
            "estimated_revision_effort": "moderate_revision" if overall >= 6 else "significant_rework",
        }

    def _validate_quality_report(self, report: dict, slide_contents: list) -> dict:
        """Ensure the quality report has all required fields."""
        if not isinstance(report.get("overall_deck_score"), (int, float)):
            slide_reviews = report.get("slide_reviews", [])
            if slide_reviews:
                scores = [r.get("slide_score", 7.0) for r in slide_reviews]
                report["overall_deck_score"] = round(sum(scores) / len(scores), 2)
            else:
                report["overall_deck_score"] = 6.5

        report.setdefault("overall_assessment", "Quality review complete.")
        report.setdefault("ready_for_client", report["overall_deck_score"] >= 7.5)
        report.setdefault("critical_issues", [])
        report.setdefault("slide_reviews", [])
        report.setdefault("deck_level_issues", [])
        report.setdefault("strengths", [])
        report.setdefault("revision_priority", [])
        report.setdefault("estimated_revision_effort", "moderate_revision")

        for review in report["slide_reviews"]:
            review.setdefault("scores", {})
            scores = review["scores"]
            scores.setdefault("headline_quality", 7.0)
            scores.setdefault("text_density", 7.0)
            scores.setdefault("visual_balance", 7.0)
            scores.setdefault("layout_compliance", 8.0)
            scores.setdefault("insight_strength", 6.5)
            scores.setdefault("narrative_flow", 7.0)

            dim_scores = list(scores.values())
            review["slide_score"] = round(sum(dim_scores) / len(dim_scores), 2) if dim_scores else 7.0
            review["approved"] = review["slide_score"] >= PASS_THRESHOLD
            review.setdefault("flags", [])
            review.setdefault("revision_suggestions", [])
            review.setdefault("revised_headline_suggestion", None)

        return report

    def revise_weak_slides(self, quality_report: dict, slide_contents: list) -> list:
        """
        For slides that failed review, attempt to revise their headlines and content.
        Returns an updated slide_contents list.
        """
        slide_by_num = {sc["slide_number"]: sc for sc in slide_contents}
        revisions = 0

        for review in quality_report.get("slide_reviews", []):
            if review.get("approved"):
                continue

            slide_num = review.get("slide_number")
            slide_content = slide_by_num.get(slide_num)
            if not slide_content:
                continue

            # Apply revised headline if provided
            revised_headline = review.get("revised_headline_suggestion")
            if revised_headline and len(revised_headline.strip()) > 5:
                slide_content["headline"] = revised_headline.strip()
                self.logger.info(f"Revised headline for slide {slide_num}: {revised_headline[:60]}")
                revisions += 1

            # Apply text density fix: trim bullets
            bullets = slide_content.get("supporting_points", [])
            # Trim long bullets
            trimmed = []
            for b in bullets[:5]:
                words = b.split()
                if len(words) > 18:
                    trimmed.append(" ".join(words[:18]) + "…")
                else:
                    trimmed.append(b)
            slide_content["supporting_points"] = trimmed

        self.logger.info(f"Slide revision pass: {revisions} headlines revised.")
        return list(slide_by_num.values())

    def execute(self, state: dict) -> AgentResult:
        """
        Execute quality review of the complete deck.

        State keys consumed: slide_contents, blueprint, intent_spec
        State keys produced: quality_report, slides_requiring_revision, approved_slides
        """
        try:
            slide_contents = state.get("slide_contents", [])
            blueprint = state.get("blueprint", {})
            intent_spec = state.get("intent_spec", {})

            if not slide_contents:
                return AgentResult(
                    success=False,
                    data=None,
                    error="SlideCriticAgent requires 'slide_contents' in state.",
                )

            # Run LLM-powered quality review
            quality_report = self.review_deck_with_llm(slide_contents, blueprint, intent_spec)

            # Apply automatic revisions to weak slides
            revised_contents = self.revise_weak_slides(quality_report, slide_contents)

            slides_requiring_revision = [
                r["slide_number"] for r in quality_report.get("slide_reviews", [])
                if not r.get("approved")
            ]
            approved_slides = [
                r["slide_number"] for r in quality_report.get("slide_reviews", [])
                if r.get("approved")
            ]

            overall_score = quality_report.get("overall_deck_score", 0)
            ready = quality_report.get("ready_for_client", False)

            self.logger.info(
                f"Critic review complete: score={overall_score:.1f}/10 | "
                f"approved={len(approved_slides)} | needs_revision={len(slides_requiring_revision)} | "
                f"client_ready={ready}"
            )

            return AgentResult(
                success=True,
                data={
                    "quality_report": quality_report,
                    "slide_contents": revised_contents,  # Updated with revisions
                    "slides_requiring_revision": slides_requiring_revision,
                    "approved_slides": approved_slides,
                },
                metadata={
                    "overall_score": overall_score,
                    "ready_for_client": ready,
                    "slides_approved": len(approved_slides),
                    "slides_revised": len(slides_requiring_revision),
                },
            )

        except Exception as e:
            self.logger.error(f"SlideCriticAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
