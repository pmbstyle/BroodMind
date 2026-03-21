from __future__ import annotations

import json
from pathlib import Path

from broodmind.tools.skills.management import (
    _load_skill_inventory,
    _tool_add_skill,
    _tool_list_skills,
    get_registered_skill_tools,
)


def test_load_skill_inventory_auto_discovers_bundle(tmp_path: Path, monkeypatch) -> None:
    workspace_dir = tmp_path / "workspace"
    skill_dir = workspace_dir / "skills" / "image-lab"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: image-lab
description: Generate images from prompts
scope: worker
---

# Image Lab
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("BROODMIND_WORKSPACE_DIR", str(workspace_dir))

    inventory = _load_skill_inventory(workspace_dir)

    assert len(inventory) == 1
    assert inventory[0]["id"] == "image-lab"
    assert inventory[0]["source"] == "bundle"
    assert inventory[0]["auto_discovered"] is True
    assert inventory[0]["scope"] == "worker"
    assert inventory[0]["exists"] is True


def test_load_skill_inventory_prefers_registry_override(tmp_path: Path, monkeypatch) -> None:
    workspace_dir = tmp_path / "workspace"
    skill_dir = workspace_dir / "skills" / "image-lab"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: image-lab
description: Generate images from prompts
---
""",
        encoding="utf-8",
    )
    (workspace_dir / "skills" / "registry.json").write_text(
        json.dumps(
            {
                "version": 1,
                "skills": [
                    {
                        "id": "image-lab",
                        "name": "Image Lab Override",
                        "description": "Registry override wins",
                        "path": "skills/image-lab/SKILL.md",
                        "scope": "queen",
                        "enabled": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BROODMIND_WORKSPACE_DIR", str(workspace_dir))

    inventory = _load_skill_inventory(workspace_dir)

    assert len(inventory) == 1
    assert inventory[0]["id"] == "image-lab"
    assert inventory[0]["source"] == "registry"
    assert inventory[0]["name"] == "image-lab"
    assert inventory[0]["description"] == "Generate images from prompts"
    assert inventory[0]["scope"] == "queen"
    assert inventory[0]["enabled"] is False


def test_load_skill_inventory_keeps_legacy_registry_skill(tmp_path: Path, monkeypatch) -> None:
    workspace_dir = tmp_path / "workspace"
    legacy_dir = workspace_dir / "legacy"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "skill.md").write_text("# Legacy\n", encoding="utf-8")
    (workspace_dir / "skills").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "skills" / "registry.json").write_text(
        json.dumps(
            {
                "version": 1,
                "skills": [
                    {
                        "id": "legacy_tooling",
                        "name": "Legacy Tooling",
                        "description": "Legacy registry entry",
                        "path": "legacy/skill.md",
                        "scope": "both",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BROODMIND_WORKSPACE_DIR", str(workspace_dir))

    inventory = _load_skill_inventory(workspace_dir)

    assert len(inventory) == 1
    assert inventory[0]["id"] == "legacy_tooling"
    assert inventory[0]["source"] == "registry"
    assert inventory[0]["exists"] is True


def test_add_skill_can_infer_name_and_description_from_skill_file(tmp_path: Path, monkeypatch) -> None:
    workspace_dir = tmp_path / "workspace"
    skill_dir = workspace_dir / "skills" / "writer"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: writer
description: Helps write copy
---
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("BROODMIND_WORKSPACE_DIR", str(workspace_dir))

    payload = json.loads(_tool_add_skill({"path": "skills/writer"}, {}))

    assert payload["status"] == "added"
    listed = json.loads(_tool_list_skills({}, {}))
    assert listed["count"] == 1
    assert listed["skills"][0]["name"] == "writer"
    assert listed["skills"][0]["description"] == "Helps write copy"


def test_registered_skill_tools_include_auto_discovered_enabled_bundle(tmp_path: Path, monkeypatch) -> None:
    workspace_dir = tmp_path / "workspace"
    skill_dir = workspace_dir / "skills" / "writer"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: writer
description: Helps write copy
---
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("BROODMIND_WORKSPACE_DIR", str(workspace_dir))

    tools = get_registered_skill_tools()

    assert [tool.name for tool in tools] == ["skill_writer"]
    assert "Helps write copy" in tools[0].description
