"""
ImageIntelligenceAgent — Fetches contextually relevant images for slide backgrounds/visuals.
Primary source: Unsplash API. Fallback: Pexels API. Final fallback: matplotlib abstract generation.
Applies content filters: prefers abstract/conceptual imagery, avoids faces for professional slides.
Caches downloaded images to avoid repeated API calls for similar queries.
"""

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class ImageIntelligenceAgent(BaseAgent):
    """
    Fetches or generates contextual images for presentation slides.

    Input state keys:
        slide_contents (list): Per-slide content for generating search queries
        intent_spec (dict): Deck context for image style guidance
        image_style (str, optional): 'abstract'|'conceptual'|'business'|'data'

    Output (AgentResult.data):
        {
          image_files: {
            slide_number: {path, source, query, attribution}
          }
        }
    """

    def __init__(self):
        super().__init__(
            name="ImageIntelligenceAgent",
            description="Fetches/generates contextual slide images from Unsplash, Pexels, or matplotlib",
        )
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        self.cache_dir = Path(os.getenv("ASSETS_DIR", "./assets")) / "images" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output")) / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()[:16]

    def _cached_path(self, query: str) -> Optional[Path]:
        key = self._cache_key(query)
        for ext in ("jpg", "jpeg", "png"):
            p = self.cache_dir / f"{key}.{ext}"
            if p.exists():
                return p
        return None

    def generate_search_query(self, slide_content: dict, intent_spec: dict) -> str:
        """
        Use LLM to generate an optimal image search query for the slide topic.
        Falls back to keyword extraction if LLM fails.
        """
        headline = slide_content.get("headline", "")
        takeaway = slide_content.get("takeaway", "")
        themes = intent_spec.get("key_themes", [])

        system = (
            "You generate concise image search queries for professional presentations. "
            "Return only 3-5 search keywords (no sentences). "
            "Prefer abstract, conceptual imagery. Avoid human faces. "
            "Good examples: 'digital transformation abstract technology', "
            "'supply chain logistics aerial view', 'data analytics visualization dark'. "
            "Bad examples: 'business meeting', 'people shaking hands', 'team working'."
        )
        user = (
            f"Slide headline: {headline}\n"
            f"Key takeaway: {takeaway}\n"
            f"Deck themes: {', '.join(themes[:3])}\n\n"
            f"Generate the best 3-5 keyword search query for an abstract/conceptual image."
        )

        try:
            query = self.llm.complete(system_prompt=system, user_message=user, max_tokens=60, temperature=0.5)
            # Clean up any punctuation or markdown
            query = re.sub(r"[\"'`\n]", " ", query).strip()
            return query[:100]
        except Exception as e:
            self.logger.warning(f"LLM query generation failed: {e}; using keyword fallback.")
            words = re.findall(r"\b[a-zA-Z]{4,}\b", headline)[:4]
            return " ".join(words) + " abstract" if words else "business technology abstract"

    def _download_image(self, url: str, dest_path: Path, headers: dict = None) -> bool:
        """Download image from URL to dest_path. Returns True on success."""
        try:
            import requests
            resp = requests.get(url, headers=headers or {}, timeout=15, stream=True)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            self.logger.warning(f"Image download failed from {url}: {e}")
            return False

    def fetch_from_unsplash(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Fetch image from Unsplash API.
        Returns (file_path, attribution) or None if unavailable.
        """
        if not self.unsplash_key:
            return None

        cached = self._cached_path(query)
        if cached:
            return str(cached), "Unsplash (cached)"

        try:
            import requests
            params = {
                "query": query,
                "per_page": 5,
                "orientation": "landscape",
                "content_filter": "high",
            }
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params=params, headers=headers, timeout=10
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

            if not results:
                return None

            # Pick the best result (prefer abstract, landscapes)
            photo = results[0]
            img_url = photo["urls"].get("regular") or photo["urls"]["full"]
            attribution = f"Photo by {photo['user']['name']} on Unsplash"

            cache_key = self._cache_key(query)
            dest = self.cache_dir / f"{cache_key}.jpg"
            success = self._download_image(img_url, dest, headers)
            if success:
                return str(dest), attribution

        except Exception as e:
            self.logger.warning(f"Unsplash fetch failed for '{query}': {e}")

        return None

    def fetch_from_pexels(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Fetch image from Pexels API.
        Returns (file_path, attribution) or None.
        """
        if not self.pexels_key:
            return None

        cached = self._cached_path(f"pexels_{query}")
        if cached:
            return str(cached), "Pexels (cached)"

        try:
            import requests
            headers = {"Authorization": self.pexels_key}
            params = {"query": query, "per_page": 5, "orientation": "landscape"}
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            photos = resp.json().get("photos", [])

            if not photos:
                return None

            photo = photos[0]
            img_url = photo["src"].get("large") or photo["src"]["original"]
            attribution = f"Photo by {photo['photographer']} on Pexels"

            cache_key = self._cache_key(f"pexels_{query}")
            dest = self.cache_dir / f"{cache_key}.jpg"
            success = self._download_image(img_url, dest, {"Authorization": self.pexels_key})
            if success:
                return str(dest), attribution

        except Exception as e:
            self.logger.warning(f"Pexels fetch failed for '{query}': {e}")

        return None

    def fetch_from_openai(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Generate image using OpenAI DALL-E API.
        Returns (file_path, attribution) or None.
        """
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            return None

        cached = self._cached_path(f"openai_{query}")
        if cached:
            return str(cached), "DALL-E (cached)"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"Professional abstract presentation background illustration: {query}. High resolution, corporate aesthetic, sleek design, gradient.",
                size="1024x1024",
                quality="standard",
                n=1,
            )
            img_url = response.data[0].url
            attribution = "Generated by OpenAI DALL-E"

            cache_key = self._cache_key(f"openai_{query}")
            dest = self.cache_dir / f"{cache_key}.jpg"
            success = self._download_image(img_url, dest)
            if success:
                return str(dest), attribution

        except Exception as e:
            self.logger.warning(f"OpenAI DALL-E generation failed for '{query}': {e}")

        return None

    def generate_abstract_visual(self, query: str, slide_num: int, theme: str = "default") -> Tuple[str, str]:
        """
        Generate a matplotlib abstract visual as a fallback image.
        Creates a gradient/pattern image appropriate for slide backgrounds.
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import numpy as np

        # Load brand colors
        config_path = Path(__file__).parent.parent / "config" / "brand_config.json"
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
            theme_cfg = cfg.get("themes", {}).get(theme, {})
            primary_hex = theme_cfg.get("primary_color", "#002060")
            secondary_hex = theme_cfg.get("secondary_color", "#00B0F0")
            accent_hex = theme_cfg.get("accent_color", "#FF6B35")
        except Exception:
            primary_hex, secondary_hex, accent_hex = "#002060", "#00B0F0", "#FF6B35"

        def hex_to_rgb01(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

        c1 = hex_to_rgb01(primary_hex)
        c2 = hex_to_rgb01(secondary_hex)
        c3 = hex_to_rgb01(accent_hex)

        fig, ax = plt.subplots(figsize=(10, 5.6))
        fig.patch.set_facecolor(c1)
        ax.set_facecolor(c1)

        np.random.seed(hash(query) % 2**31)
        for _ in range(12):
            x = np.random.uniform(0, 10)
            y = np.random.uniform(0, 5.6)
            r = np.random.uniform(0.3, 1.8)
            color = [c2, c3][np.random.randint(0, 2)]
            alpha = np.random.uniform(0.05, 0.18)
            circle = patches.Circle((x, y), r, color=color, alpha=alpha)
            ax.add_patch(circle)

        # Grid lines for abstract tech feel
        for x in np.arange(0, 10, 1.2):
            ax.axvline(x, color=c2, alpha=0.07, linewidth=0.5)
        for y in np.arange(0, 5.6, 0.8):
            ax.axhline(y, color=c2, alpha=0.07, linewidth=0.5)

        ax.set_xlim(0, 10)
        ax.set_ylim(0, 5.6)
        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        dest = self.output_dir / f"abstract_slide_{slide_num:02d}.png"
        fig.savefig(str(dest), dpi=120, bbox_inches="tight", facecolor=c1)
        plt.close(fig)

        return str(dest), "Generated abstract visual (DeckClaude)"

    def fetch_image_for_slide(
        self, slide_content: dict, intent_spec: dict, slide_num: int
    ) -> dict:
        """
        Fetch or generate an image for a single slide.
        Returns {path, source, query, attribution}.
        """
        query = self.generate_search_query(slide_content, intent_spec)
        theme = intent_spec.get("recommended_theme", "default")

        result = self.fetch_from_unsplash(query)
        if result:
            path, attribution = result
            return {"path": path, "source": "unsplash", "query": query, "attribution": attribution}

        result = self.fetch_from_pexels(query)
        if result:
            path, attribution = result
            return {"path": path, "source": "pexels", "query": query, "attribution": attribution}

        # OpenAI DALL-E fallback
        result = self.fetch_from_openai(query)
        if result:
            path, attribution = result
            return {"path": path, "source": "openai", "query": query, "attribution": attribution}

        path, attribution = self.generate_abstract_visual(query, slide_num, theme)
        return {"path": path, "source": "generated", "query": query, "attribution": attribution}

    def execute(self, state: dict) -> AgentResult:
        """
        Fetch images for all image-type slides.

        State keys consumed: slide_contents, intent_spec
        State keys produced: image_files
        """
        try:
            slide_contents = state.get("slide_contents", [])
            intent_spec = state.get("intent_spec", {})
            # Read include_images from state directly (set by API request) with fallback to intent_spec
            include_images = state.get("include_images", intent_spec.get("include_images", True))
            image_files = {}

            if not include_images:
                self.logger.info("Image inclusion disabled; skipping ImageAgent.")
                return AgentResult(
                    success=True,
                    data={"image_files": {}},
                    metadata={"skipped": True},
                )

            # Use visual_plan (from DesignAgent) to find slides marked for images.
            # Fall back to heuristic selection if visual_plan is unavailable.
            visual_plan = state.get("visual_plan", [])
            image_slide_nums = {
                p["slide_number"] for p in visual_plan if p.get("needs_image_agent")
            }

            eligible = []
            for slide in slide_contents:
                slide_num = slide.get("slide_number")
                if slide_num is None:
                    continue

                if image_slide_nums:
                    # Trust the DesignAgent's plan
                    if slide_num in image_slide_nums:
                        eligible.append(slide)
                else:
                    # Fallback heuristic: title/section/image slides + content without charts
                    slide_type = slide.get("slide_type", "content")
                    chart_type = (slide.get("visual_data") or {}).get("chart_type", "none")
                    has_chart = chart_type not in ("none", None, "")
                    if slide_type in ("title", "section", "image_content") or (
                        slide_type == "content" and not has_chart
                    ):
                        eligible.append(slide)

            # Cap at 8 images to avoid API rate limits
            selected_slides = eligible[:8]
            self.logger.info(f"ImageAgent: fetching images for {len(selected_slides)} of {len(slide_contents)} slides.")

            for slide in selected_slides:
                slide_num = slide.get("slide_number")
                self.logger.info(f"Fetching image for slide {slide_num}...")
                image_info = self.fetch_image_for_slide(slide, intent_spec, slide_num)
                image_files[slide_num] = image_info
                # Courtesy delay for external APIs
                if image_info["source"] in ("unsplash", "pexels"):
                    time.sleep(0.4)

            self.logger.info(f"ImageAgent: {len(image_files)} images acquired.")
            return AgentResult(
                success=True,
                data={"image_files": image_files},
                metadata={"images_fetched": len(image_files)},
            )

        except Exception as e:
            self.logger.error(f"ImageIntelligenceAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
