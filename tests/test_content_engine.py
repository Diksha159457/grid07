from grid07.content_engine import ContentEngine


def test_content_engine_returns_structured_payload() -> None:
    engine = ContentEngine()
    payload = engine.generate_post("bot_a")
    assert payload["bot_id"] == "bot_a"
    assert payload["search_query"]
    assert payload["source_headline"]
    assert len(payload["post_content"]) <= 280
    assert engine.graph is not None
