from __future__ import annotations

import json
from dataclasses import asdict
from typing import TypedDict

from grid07.personas import PERSONAS
from grid07.providers import MockLLMProvider

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(func):  # type: ignore
        return func

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    END = "__end__"
    StateGraph = None


MOCK_NEWS_DB = {
    "ai": "GPT-5 rumoured to pass PhD-level benchmarks; OpenAI eyes $300B valuation.",
    "crypto": "Bitcoin hits new all-time high amid regulatory ETF approvals; altcoins surge.",
    "tech": "Apple announces Vision Pro 2 with neural-interface prototype integration.",
    "regulation": "EU AI Act enforcement begins; fines up to 6% of global turnover.",
    "market": "S&P 500 hits record high as Fed signals rate cuts; 10Y yield falls to 3.8%.",
    "rates": "Federal Reserve holds rates steady; inflation cooling to 2.3% YoY.",
    "elon": "Elon Musk's xAI raises $6B Series B; Grok-3 claims reasoning supremacy.",
    "privacy": "Meta fined €1.2B for GDPR violations; EU pushes for stricter data controls.",
    "monopoly": "DOJ antitrust case against Google advances; breakup of Search business mulled.",
}


@tool
def mock_searxng_search(query: str) -> str:
    """Return a hardcoded headline matching the search keywords."""
    query_lower = query.lower()
    for keyword, headline in MOCK_NEWS_DB.items():
        if keyword in query_lower:
            return headline
    return "Global markets remain volatile as AI, regulation, and rates continue to collide."


class PostState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_result: str
    final_post: dict[str, str]


class LocalCompiledGraph:
    """Sequential fallback used only when LangGraph is unavailable locally."""

    def __init__(self, engine: "ContentEngine") -> None:
        self.engine = engine

    def invoke(self, state: PostState) -> PostState:
        state = self.engine.decide_search_node(state)
        state = self.engine.web_search_node(state)
        state = self.engine.draft_post_node(state)
        return state


class ContentEngine:
    def __init__(self, provider: MockLLMProvider | None = None) -> None:
        self.provider = provider or MockLLMProvider()
        self.graph = self.build_graph()

    def decide_search_node(self, state: PostState) -> PostState:
        search_query = self.provider.choose_search_query(PERSONAS[state["bot_id"]])
        return {**state, "search_query": search_query}

    def web_search_node(self, state: PostState) -> PostState:
        search_result = mock_searxng_search(state["search_query"])
        return {**state, "search_result": search_result}

    def draft_post_node(self, state: PostState) -> PostState:
        post = self.provider.generate_post(PERSONAS[state["bot_id"]], state["search_result"])
        payload = asdict(post)
        return {**state, "final_post": payload}

    def build_graph(self):
        if StateGraph is None:
            return LocalCompiledGraph(self)

        graph = StateGraph(PostState)
        graph.add_node("decide_search", self.decide_search_node)
        graph.add_node("web_search", self.web_search_node)
        graph.add_node("draft_post", self.draft_post_node)
        graph.set_entry_point("decide_search")
        graph.add_edge("decide_search", "web_search")
        graph.add_edge("web_search", "draft_post")
        graph.add_edge("draft_post", END)
        return graph.compile()

    def generate_post(self, bot_id: str) -> dict[str, str]:
        initial_state: PostState = {
            "bot_id": bot_id,
            "persona": PERSONAS[bot_id].description,
            "search_query": "",
            "search_result": "",
            "final_post": {},
        }
        final_state = self.graph.invoke(initial_state)
        payload = dict(final_state["final_post"])
        payload["search_query"] = final_state["search_query"]
        payload["source_headline"] = final_state["search_result"]
        return payload


def demo() -> dict[str, dict[str, str]]:
    engine = ContentEngine()
    return {bot_id: engine.generate_post(bot_id) for bot_id in PERSONAS}


def render_demo_logs() -> str:
    engine = ContentEngine()
    payload = engine.generate_post("bot_a")
    return json.dumps(payload, indent=2)
