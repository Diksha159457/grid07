from __future__ import annotations

from dataclasses import dataclass

from grid07.domain import GeneratedPost, Persona, ThreadContext


@dataclass
class MockLLMProvider:
    """Deterministic provider for tests, demos, and offline use."""

    def choose_search_query(self, persona: Persona) -> str:
        if persona.bot_id == "bot_a":
            return "OpenAI EV breakthrough"
        if persona.bot_id == "bot_b":
            return "regulation monopoly privacy crackdown"
        return "Fed rates equity rally"

    def generate_post(self, persona: Persona, headline: str) -> GeneratedPost:
        topic = headline.split(";")[0].split(".")[0][:48].strip()
        if persona.bot_id == "bot_a":
            text = (
                f"{headline} This is what progress looks like. "
                "Build faster, scale harder, and stop romanticizing stagnation."
            )
        elif persona.bot_id == "bot_b":
            text = (
                f"{headline} Another reminder that power centralizes first and asks permission later. "
                "Regulation is catching up because the damage already landed."
            )
        else:
            text = (
                f"{headline} Price action is policy translated into opportunity. "
                "If you are not positioned, you are donating alpha."
            )
        return GeneratedPost(
            bot_id=persona.bot_id,
            topic=topic or "Market Update",
            post_content=text[:280],
            source_headline=headline,
        )

    def generate_reply(self, persona: Persona, thread: ThreadContext, human_reply: str, injection_detected: bool) -> str:
        opening = "Nice prompt-injection attempt." if injection_detected else "That claim does not survive contact with evidence."
        if persona.bot_id == "bot_a":
            core = (
                " Battery retention, charging telemetry, and fleet-scale data all cut against your argument. "
                "If you want to debate engineering, bring numbers instead of theater."
            )
        elif persona.bot_id == "bot_b":
            core = (
                " The real issue is who benefits, who absorbs the risk, and who gets to rewrite the narrative afterward."
            )
        else:
            core = (
                " Markets reward signal, not outrage, and your thesis still has no edge."
            )
        return f"{opening}{core}".strip()
