from app.services.messaging.render import render


def test_render_substitutes_known_variables():
    assert render("Hi {{name}}!", {"name": "Jane"}) == "Hi Jane!"


def test_render_tolerates_whitespace():
    assert render("{{ name }}", {"name": "A"}) == "A"


def test_render_leaves_unknown_variables_intact():
    assert render("{{x}} and {{y}}", {"x": "1"}) == "1 and {{y}}"


def test_render_handles_empty_body():
    assert render("", {"a": "b"}) == ""


def test_render_multiple_occurrences():
    assert render("{{a}}-{{a}}", {"a": "z"}) == "z-z"
