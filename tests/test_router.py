from grid07.router import PersonaRouter, route_post_to_bots


def test_finance_post_routes_to_bot_c() -> None:
    router = PersonaRouter(use_semantic_router=False, threshold=0.2)
    matches = router.route("The Fed paused hikes and bond yields dropped after inflation cooled.")
    assert matches
    assert matches[0].bot_id == "bot_c"


def test_regulation_post_routes_to_bot_b() -> None:
    router = PersonaRouter(use_semantic_router=False, threshold=0.2)
    matches = router.route("Regulators are finally challenging platform monopolies and surveillance.")
    assert matches
    assert matches[0].bot_id == "bot_b"


def test_assignment_helper_returns_list() -> None:
    matches = route_post_to_bots(
        "OpenAI just released a new model that might replace junior developers.",
        threshold=0.2,
    )
    assert matches
    assert matches[0]["bot_id"] == "bot_a"
