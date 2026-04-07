from __future__ import annotations

import asyncio
import json
from pathlib import Path

from octopal.cli.configure import _ensure_workspace_bootstrap
from octopal.runtime.octo.prompt_builder import build_bootstrap_context_prompt
from octopal.runtime.workers.loader import discover_worker_templates


def test_workspace_bootstrap_creates_required_markdown(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _ensure_workspace_bootstrap(workspace)

    assert (workspace / "AGENTS.md").exists()
    assert (workspace / "USER.md").exists()
    assert (workspace / "SOUL.md").exists()
    assert (workspace / "HEARTBEAT.md").exists()
    assert (workspace / "MEMORY.md").exists()
    assert (workspace / "memory" / "canon" / "facts.md").exists()
    assert (workspace / "memory" / "canon" / "decisions.md").exists()
    assert (workspace / "memory" / "canon" / "failures.md").exists()
    assert (workspace / "experiments" / "README.md").exists()
    assert (workspace / "experiments" / "results.jsonl").exists()
    assert (workspace / "workers" / "web_fetcher" / "worker.json").exists()
    assert (workspace / "workers" / "web_researcher" / "worker.json").exists()

    assert "## User" in (workspace / "USER.md").read_text(encoding="utf-8")
    assert "## Persona" in (workspace / "SOUL.md").read_text(encoding="utf-8")
    assert "# HEARTBEAT" in (workspace / "HEARTBEAT.md").read_text(encoding="utf-8")
    agents_content = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert "Core Roles" in agents_content
    assert "Safety Rules" in agents_content
    assert "HEARTBEAT_OK" in agents_content
    assert "Controlled Self-Improvement" in agents_content
    assert "Workers are the default path for external work." in agents_content
    assert "do not reduce `timeout_seconds` below the worker template default" in agents_content
    assert "prefer a worker that can spawn child workers or launch a bounded parallel batch" in agents_content


def test_bootstrap_context_includes_experiments_readme(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    _ensure_workspace_bootstrap(workspace)
    monkeypatch.setenv("OCTOPAL_WORKSPACE_DIR", str(workspace))

    context = asyncio.run(build_bootstrap_context_prompt(store=None, chat_id=123))

    assert 'file name="experiments/README.md"' in context.content
    assert "one active experiment at a time" in context.content


def test_workspace_bootstrap_is_non_destructive(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    user_file = workspace / "USER.md"
    user_file.write_text("existing", encoding="utf-8")

    _ensure_workspace_bootstrap(workspace)

    assert user_file.read_text(encoding="utf-8") == "existing"


def test_workspace_bootstrap_syncs_all_default_worker_templates(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _ensure_workspace_bootstrap(workspace)

    source_ids = {
        path.parent.name
        for path in (Path("workspace_templates") / "workers").glob("*/worker.json")
    }
    target_ids = {
        path.parent.name
        for path in (workspace / "workers").glob("*/worker.json")
    }

    assert target_ids == source_ids


def test_bootstrap_worker_templates_align_with_current_runtime_expectations(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _ensure_workspace_bootstrap(workspace)

    templates = {template.id: template for template in discover_worker_templates(workspace)}

    assert "research_coordinator" in templates
    assert templates["research_coordinator"].can_spawn_children is True
    assert "start_child_worker" in templates["research_coordinator"].available_tools
    assert "start_workers_parallel" in templates["research_coordinator"].available_tools
    assert "web_researcher" in templates["research_coordinator"].allowed_child_templates

    assert "fetch_plan_tool" in templates["web_fetcher"].available_tools
    assert "markdown_new_fetch" in templates["web_fetcher"].available_tools
    assert "fetch_plan_tool" in templates["web_researcher"].available_tools

    assert "test_run" in templates["coder"].available_tools
    assert "fs_write" in templates["writer"].available_tools
    assert "fs_read" in templates["analyst"].available_tools

    raw_coordinator = json.loads(
        (workspace / "workers" / "research_coordinator" / "worker.json").read_text(encoding="utf-8")
    )
    assert raw_coordinator["required_permissions"] == ["worker_manage"]
