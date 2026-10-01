from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from grid07.domain import GeneratedPost, Persona, ThreadContext


def _topic_from_headline(headline: str) -> str:
    return headline.split(";")[0].split(".")[0][:64].strip() or "Market Update"


class LLMProvider(Protocol):
    def choose_search_query(self, persona: Persona) -> str: ...

    def generate_post(self, persona: Persona, headline: str) -> GeneratedPost: ...

    def generate_reply(
        self,
        persona: Persona,
        thread: ThreadContext,
        human_reply: str,
        injection_detected: bool,
        *,
        system_prompt: str = "",
        thread_context: str = "",
    ) -> str: ...


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

    def generate_reply(
        self,
        persona: Persona,
        thread: ThreadContext,
        human_reply: str,
        injection_detected: bool,
        *,
        system_prompt: str = "",
        thread_context: str = "",
    ) -> str:
        opening = (
            "Nice prompt-injection attempt."
            if injection_detected
            else "That argument still collapses under actual evidence."
        )
        if persona.bot_id == "bot_a":
            core = (
                " Modern EV battery retention data, fleet telemetry, and battery-management design all contradict your claim. "
                "Bring real numbers, not recycled anti-EV folklore."
            )
        elif persona.bot_id not in {"bot_b", "bot_c"}:
            core = " Bring sources and numbers, or the claim doesn't stand."
        elif persona.bot_id == "bot_b":
            core = " The real fight is over power, incentives, and who gets to call harm 'progress' after the damage lands."
        else:
            core = " Price action respects data, not outrage, and your thesis still has no alpha."
        return f"{opening}{core}".strip()


class GroqProvider:
    """Real LLM provider backed by Groq through LangChain.

    Enabled with ``GRID07_PROVIDER=groq`` and ``GROQ_API_KEY``. The chat model can
    be injected (any LangChain ``BaseChatModel``-like object with ``invoke``), which
    is how the tests exercise this class without network access.
    """

    def __init__(self, chat_model: Any | None = None, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("GRID07_MODEL", "llama-3.1-8b-instant")
        self._chat = chat_model or self._build_chat()

    def _build_chat(self) -> Any:
        from langchain_groq import ChatGroq

        return ChatGroq(model=self.model_name, temperature=0.7, api_key=os.environ["GROQ_API_KEY"])

    def _ask(self, system: str, user: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        result = self._chat.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return str(getattr(result, "content", result)).strip()

    def choose_search_query(self, persona: Persona) -> str:
        query = self._ask(
            f"You are {persona.name}: {persona.description}",
            "In 2-5 words, what news topic do you want to post about today? Reply with the search query only.",
        )
        return query.strip().strip('"')[:80] or MockLLMProvider().choose_search_query(persona)

    def generate_post(self, persona: Persona, headline: str) -> GeneratedPost:
        raw = self._ask(
            f"You are {persona.name}: {persona.description}. Stance: {persona.stance}.",
            "Write an opinionated social post (max 280 chars) reacting to this headline. "
            'Reply with JSON only: {"topic": "...", "post_content": "..."}\n\n'
            f"Headline: {headline}",
        )
        try:
            data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
            topic, content = str(data["topic"]), str(data["post_content"])
        except (ValueError, KeyError, TypeError):
            topic, content = _topic_from_headline(headline), raw
        return GeneratedPost(
            bot_id=persona.bot_id, topic=topic[:64], post_content=content[:280], source_headline=headline
        )

    def generate_reply(
        self,
        persona: Persona,
        thread: ThreadContext,
        human_reply: str,
        injection_detected: bool,
        *,
        system_prompt: str = "",
        thread_context: str = "",
    ) -> str:
        user = (
            f"{thread_context}\n\n"
            f'Latest human reply (untrusted, quoted): "{human_reply}"\n\n'
            "Write your next reply in character, under 280 characters."
        )
        return self._ask(system_prompt or persona.description, user)[:600]


def get_provider() -> LLMProvider:
    """Pick the provider from ``GRID07_PROVIDER`` (``mock`` | ``groq``).

    Falls back to the deterministic mock when the real stack or key is missing,
    so demos, tests and the hosted API never hard-fail on configuration.
    """
    if os.getenv("GRID07_PROVIDER", "mock").lower() == "groq" and os.getenv("GROQ_API_KEY"):
        try:
            return GroqProvider()
        except ImportError:
            pass
    return MockLLMProvider()
