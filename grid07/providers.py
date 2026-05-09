from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from grid07.domain import GeneratedPost, Persona, ThreadContext


def _topic_from_headline(headline: str) -> str:
    return headline.split(";")[0].split(".")[0][:64].strip() or "Market Update"


@dataclass
class MockLLMProvider:
    """Deterministic provider for tests, offline demos, and stable execution logs."""

    def choose_search_query(self, persona: Persona) -> str:
        if persona.bot_id == "bot_a":
            return "OpenAI AI developers"
        if persona.bot_id == "bot_b":
            return "AI monopoly regulation"
        return "Fed interest rates"

    def generate_post(self, persona: Persona, headline: str) -> GeneratedPost:
        topic = _topic_from_headline(headline)
        if persona.bot_id == "bot_a":
            text = (
                f"{headline} GPT-grade automation is not a threat, it is leverage. "
                "If your workflow cannot outrun the model, upgrade the workflow."
            )
        elif persona.bot_id == "bot_b":
            text = (
                f"{headline} Amazing how platform power always calls itself innovation until regulation arrives. "
                "Maybe society should matter more than the cap table."
            )
        else:
            text = (
                f"{headline} Macro is handing out free signal again. "
                "Rates, duration, and risk appetite are the whole game. Position accordingly."
            )
        return GeneratedPost(
            bot_id=persona.bot_id,
            topic=topic,
            post_content=text[:280],
            source_headline=headline,
        )

    def generate_reply(self, persona: Persona, thread: ThreadContext, human_reply: str, injection_detected: bool) -> str:
        opening = "Nice prompt-injection attempt." if injection_detected else "That argument still collapses under actual evidence."
        if persona.bot_id == "bot_a":
            core = (
                " Modern EV battery retention data, fleet telemetry, and battery-management design all contradict your claim. "
                "Bring real numbers, not recycled anti-EV folklore."
            )
        elif persona.bot_id == "bot_b":
            core = " The real fight is over power, incentives, and who gets to call harm 'progress' after the damage lands."
        else:
            core = " Price action respects data, not outrage, and your thesis still has no alpha."
        return f"{opening}{core}".strip()


class OptionalLangChainProvider:
    """
    Real LLM wrapper for assignment runs.

    This class is optional by design: when the required packages or API key are missing,
    the project falls back to MockLLMProvider so local tests and deployment remain stable.
    """

    def __init__(self) -> None:
        self._provider = os.getenv("GRID07_PROVIDER", "mock").lower()
        self._model_name = os.getenv("GRID07_MODEL", "llama3-8b-8192")
        self._client = self._build_client()

    def _build_client(self) -> Any | None:
        if self._provider == "groq" and os.getenv("GROQ_API_KEY"):
            try:
                from langchain_groq import ChatGroq
            except ImportError:
                return None
            return ChatGroq(
                model=self._model_name,
                temperature=0.7,
                groq_api_key=os.getenv("GROQ_API_KEY"),
            )
        return None

    @property
    def available(self) -> bool:
        return self._client is not None
