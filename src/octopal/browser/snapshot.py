from __future__ import annotations

import re
from typing import TypedDict

import structlog
from playwright.async_api import Page

logger = structlog.get_logger(__name__)

class ElementRef(TypedDict):
    role: str
    name: str | None
    nth: int

class SnapshotResult(TypedDict):
    snapshot: str
    refs: dict[str, ElementRef]

INTERACTIVE_ROLES = {
    "button", "link", "textbox", "checkbox", "radio", "combobox",
    "listbox", "menuitem", "option", "searchbox", "slider",
    "spinbutton", "switch", "tab", "treeitem"
}

def _get_indent_level(line: str) -> int:
    match = re.match(r"^(\s*)", line)
    return len(match.group(1)) // 2 if match else 0


def _fallback_snapshot_from_html(html: str) -> SnapshotResult:
    lines = []
    refs: dict[str, ElementRef] = {}
    ref_counter = 1

    # Keep this intentionally simple: enough structure for debugging when
    # aria_snapshot isn't available in the current Playwright runtime.
    for role, name in re.findall(
        r'(?is)<(?P<tag>button|a|input|textarea|select)[^>]*?(?:aria-label|title|value)?\s*=\s*"?(?P<name>[^">]+)"?[^>]*>',
        html,
    ):
        normalized_role = "link" if role.lower() == "a" else role.lower()
        ref_id = f"e{ref_counter}"
        refs[ref_id] = {"role": normalized_role, "name": name.strip() or None, "nth": 0}
        if name.strip():
            lines.append(f'- {normalized_role} "{name.strip()}" [ref={ref_id}]')
        else:
            lines.append(f"- {normalized_role} [ref={ref_id}]")
        ref_counter += 1

    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text:
        preview = text[:400]
        suffix = "..." if len(text) > 400 else ""
        lines.append(f"Text: {preview}{suffix}")

    if not lines:
        lines.append("Page snapshot unavailable")

    return {"snapshot": "\n".join(lines), "refs": refs}

async def capture_aria_snapshot(page: Page) -> SnapshotResult:
    """Capture an ARIA snapshot and inject stable references."""
    if hasattr(page, "aria_snapshot"):
        raw_snapshot = await page.aria_snapshot()
    else:
        logger.info("Page aria_snapshot unavailable; falling back to DOM-based snapshot")
        html = await page.content()
        return _fallback_snapshot_from_html(html)

    # Playwright's aria_snapshot returns a YAML-like string
    lines = raw_snapshot.splitlines()

    result_lines = []
    refs: dict[str, ElementRef] = {}

    # Track role+name counts to handle duplicates with nth()
    role_name_counts: dict[str, int] = {}

    ref_counter = 1

    for line in lines:
        # Match pattern: "  - role \"name\"" or "  - role"
        match = re.match(r'^(\s*-\s*)(\w+)(?:\s+"([^"]*)")?(.*)$', line)
        if not match:
            result_lines.append(line)
            continue

        prefix, role, name, suffix = match.groups()
        role = role.lower()

        # We only assign refs to interactive roles or things with names
        if role in INTERACTIVE_ROLES or name:
            ref_id = f"e{ref_counter}"

            # Track duplicates
            key = f"{role}:{name or ''}"
            nth = role_name_counts.get(key, 0)
            role_name_counts[key] = nth + 1

            refs[ref_id] = {
                "role": role,
                "name": name,
                "nth": nth
            }

            # Inject ref into the snapshot line for the LLM
            ref_tag = f" [ref={ref_id}]"
            if nth > 0:
                ref_tag += f" [nth={nth}]"

            new_line = f"{prefix}{role}"
            if name:
                new_line += f' "{name}"'
            new_line += f"{ref_tag}{suffix}"
            result_lines.append(new_line)
            ref_counter += 1
        else:
            result_lines.append(line)

    return {
        "snapshot": "\n".join(result_lines),
        "refs": refs
    }
