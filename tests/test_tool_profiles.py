from __future__ import annotations

from broodmind.tools.metadata import ToolMetadata, normalize_tool_tags
from broodmind.tools.profiles import DEFAULT_TOOL_PROFILES, apply_tool_profile, get_tool_profile
from broodmind.tools.registry import ToolSpec


def _tool(name: str) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=f"{name} tool",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        permission="network",
        handler=lambda _args, _ctx: "ok",
    )


def test_normalize_tool_tags_deduplicates_and_normalizes() -> None:
    assert normalize_tool_tags([" Research ", "ops", "research", "", "OPS"]) == (
        "research",
        "ops",
    )


def test_tool_metadata_normalizes_values() -> None:
    metadata = ToolMetadata(
        category=" Web ",
        profile_tags=("Research", "research", "ops"),
        capabilities=("Fetch", "fetch", "summarize"),
    )
    assert metadata.category == "web"
    assert metadata.profile_tags == ("research", "ops")
    assert metadata.capabilities == ("fetch", "summarize")


def test_get_tool_profile_is_case_insensitive() -> None:
    profile = get_tool_profile("Coding")
    assert profile is not None
    assert profile.name == "coding"


def test_apply_tool_profile_filters_tool_list() -> None:
    tools = [_tool("fs_read"), _tool("web_search"), _tool("service_health")]
    out = apply_tool_profile(tools, "coding")
    assert [tool.name for tool in out] == ["fs_read"]


def test_default_profiles_include_expected_foundation_profiles() -> None:
    assert {"minimal", "research", "coding", "ops", "communication"} <= set(
        DEFAULT_TOOL_PROFILES
    )
