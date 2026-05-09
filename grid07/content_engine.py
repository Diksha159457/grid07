from __future__ import annotations

from dataclasses import asdict

from grid07.domain import GeneratedPost
from grid07.personas import PERSONAS
from grid07.providers import MockLLMProvider


MOCK_NEWS_DB = {
    "ai": "OpenAI unveils a frontier coding model as enterprises accelerate AI-native development.",
    "ev": "Battery longevity data shows modern EV packs retaining strong capacity past 100,000 miles.",
    "market": "The S&P 500 rallies as cooling inflation revives expectations for rate cuts.",
    "rates": "Treasury yields ease after the latest inflation print softens the hawkish outlook.",
    "regulation": "EU regulators increase pressure on major platforms over AI transparency and monopoly risk.",
    "privacy": "Data-rights advocates push for stricter oversight after another high-profile platform breach.",
}


class MockNewsSearch:
    def search(self, query: str) -> str:
        query_lower = query.lower()
        for keyword, headline in MOCK_NEWS_DB.items():
            if keyword in query_lower:
                return headline
        return "Global markets stay restless as AI, regulation, and rates continue to collide."


class ContentEngine:
    def __init__(self, provider: MockLLMProvider | None = None, search_client: MockNewsSearch | None = None) -> None:
        self.provider = provider or MockLLMProvider()
        self.search_client = search_client or MockNewsSearch()

    def decide_search(self, bot_id: str) -> str:
        return self.provider.choose_search_query(PERSONAS[bot_id])

    def search(self, query: str) -> str:
        return self.search_client.search(query)

    def draft_post(self, bot_id: str, headline: str) -> GeneratedPost:
        return self.provider.generate_post(PERSONAS[bot_id], headline)

    def generate_post(self, bot_id: str) -> dict[str, str]:
        query = self.decide_search(bot_id)
        headline = self.search(query)
        post = self.draft_post(bot_id, headline)
        payload = asdict(post)
        payload["search_query"] = query
        return payload


def demo() -> dict[str, dict[str, str]]:
    engine = ContentEngine()
    return {bot_id: engine.generate_post(bot_id) for bot_id in PERSONAS}
