from __future__ import annotations

from broodmind.utils import extract_reaction_and_strip, strip_reaction_tags


def test_extract_reaction_and_strip_removes_tag() -> None:
    emoji, text = extract_reaction_and_strip("<react>👍</react> Hello there")
    assert emoji == "👍"
    assert text == "Hello there"


def test_strip_reaction_tags_removes_unknown_react_markup() -> None:
    cleaned = strip_reaction_tags("Text <react>not-an-emoji</react> remains")
    assert "<react>" not in cleaned
    assert "</react>" not in cleaned
    assert "Text" in cleaned
    assert "remains" in cleaned
