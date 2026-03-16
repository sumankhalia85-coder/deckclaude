"""
Base agent class and LLM client for the DeckClaude multi-agent system.
Provides: LLMClient (OpenAI/Anthropic), AgentResult dataclass, BaseAgent ABC,
JSON parsing utilities, retry logic with exponential backoff.
"""

import abc
import json
import time
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Standardized result container for all agent executions."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    execution_time: float = 0.0

    def __repr__(self) -> str:
        status = "OK" if self.success else f"ERR({self.error[:60]}...)" if self.error and len(self.error) > 60 else f"ERR({self.error})"
        return f"AgentResult({status}, exec={self.execution_time:.2f}s)"


class LLMClient:
    """
    Unified LLM client supporting Anthropic Claude and OpenAI GPT.
    Provider is controlled via LLM_PROVIDER env var (default: anthropic).
    Includes retry logic with exponential backoff on transient failures.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        self.client = self._build_client()
        logger.info(f"LLMClient initialized: provider={self.provider}, model={self.model}")

    def _build_client(self):
        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                raise ImportError("anthropic package is required. Install with: pip install anthropic")
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                raise ImportError("openai package is required. Install with: pip install openai")
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}. Use 'anthropic' or 'openai'.")

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """
        Send a completion request with retry logic (3 attempts, exponential backoff).
        Returns the text content of the response.
        """
        last_error = None
        for attempt in range(3):
            try:
                if self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_message}],
                    )
                    return response.content[0].text

                else:  # openai
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response.choices[0].message.content

            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = 2 ** attempt  # 1s, 2s
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/3), retrying in {wait}s: {type(e).__name__}: {e}"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"LLM call failed after 3 attempts: {e}")

        raise RuntimeError(f"LLM completion failed after 3 attempts. Last error: {last_error}") from last_error


class BaseAgent(abc.ABC):
    """
    Abstract base class for all DeckClaude agents.
    Provides: LLM access, JSON parsing, logging, execution timing.
    All subclasses must implement execute(state: dict) -> AgentResult.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = LLMClient()
        self.logger = logging.getLogger(f"agents.{name}")

    def parse_json(self, text: str) -> dict:
        """
        Robustly parse JSON from LLM response text.
        Attempts: (1) direct parse, (2) markdown code block extraction,
        (3) regex object extraction, (4) bracket-balanced extraction.
        Raises ValueError if all attempts fail.
        """
        # Attempt 1: direct JSON parse
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # Attempt 2: extract from markdown code block ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Attempt 3: find the outermost { ... } block
        brace_start = stripped.find("{")
        if brace_start != -1:
            depth = 0
            for i, ch in enumerate(stripped[brace_start:], start=brace_start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = stripped[brace_start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # Attempt 4: find the outermost [ ... ] block (for array responses)
        bracket_start = stripped.find("[")
        if bracket_start != -1:
            depth = 0
            for i, ch in enumerate(stripped[bracket_start:], start=bracket_start):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        candidate = stripped[bracket_start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        preview = text[:300].replace("\n", " ")
        raise ValueError(f"Could not parse JSON from LLM response. Preview: {preview}")

    def safe_execute(self, state: dict) -> AgentResult:
        """
        Wraps execute() with timing and top-level exception handling.
        Use this method externally to run agents safely.
        """
        start = time.time()
        try:
            result = self.execute(state)
            result.execution_time = time.time() - start
            self.logger.info(f"Agent '{self.name}' completed in {result.execution_time:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            self.logger.error(f"Agent '{self.name}' raised unhandled exception: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.name},
                execution_time=elapsed,
            )

    @abc.abstractmethod
    def execute(self, state: dict) -> AgentResult:
        """
        Execute the agent's task using the provided state dictionary.
        Must return an AgentResult. Should NOT raise — handle exceptions internally.
        """
