from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import structlog

from broodmind.tools.skills.bundles import (
    SkillBundle,
    discover_skill_bundle_dirs,
    load_skill_bundle,
)
from broodmind.tools.registry import ToolSpec

logger = structlog.get_logger(__name__)

_SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_DEFAULT_MAX_CHARS = 16_000
_MAX_CHARS_LIMIT = 200_000
_REGISTRY_VERSION = 1


def ensure_skills_layout(workspace_dir: Path | None = None) -> Path:
    root = workspace_dir.resolve() if workspace_dir else _workspace_root()
    skills_dir = root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    path = _registry_path(root)
    if not path.exists():
        _write_registry(root, {"version": _REGISTRY_VERSION, "skills": []})
    return path


def get_skill_management_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="list_skills",
            description="List internal skills from registry and auto-discovered skill bundles.",
            parameters={
                "type": "object",
                "properties": {
                    "include_disabled": {
                        "type": "boolean",
                        "description": "Include disabled skills in the result (default false).",
                    }
                },
                "additionalProperties": False,
            },
            permission="skill_manage",
            handler=_tool_list_skills,
        ),
        ToolSpec(
            name="add_skill",
            description="Register a new internal skill from a SKILL.md path.",
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Skill id (optional; inferred from name/path when omitted)."},
                    "name": {"type": "string", "description": "Human-friendly skill name."},
                    "description": {"type": "string", "description": "Short skill description."},
                    "path": {"type": "string", "description": "Path to SKILL.md (or its containing directory)."},
                    "scope": {
                        "type": "string",
                        "description": "Where the skill should be available.",
                        "enum": ["queen", "worker", "both"],
                    },
                    "enabled": {"type": "boolean", "description": "Whether the skill is enabled (default true)."},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            permission="skill_manage",
            handler=_tool_add_skill,
        ),
        ToolSpec(
            name="remove_skill",
            description="Remove a skill from the internal registry by id.",
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Skill id to remove."},
                },
                "required": ["id"],
                "additionalProperties": False,
            },
            permission="skill_manage",
            handler=_tool_remove_skill,
        ),
    ]


def get_registered_skill_tools() -> list[ToolSpec]:
    workspace_dir = _workspace_root()
    skills = _load_skill_inventory(workspace_dir)
    tools: list[ToolSpec] = []
    for raw in skills:
        if not bool(raw.get("enabled", True)):
            continue
        skill_id = str(raw.get("id", "")).strip()
        if not _SKILL_ID_RE.fullmatch(skill_id):
            continue
        tool_name = f"skill_{skill_id}"
        if not bool(raw.get("exists", False)):
            logger.warning("Skipping skill tool because SKILL.md is missing", skill_id=skill_id)
            continue
        name = str(raw.get("name", skill_id)).strip() or skill_id
        description = str(raw.get("description", "")).strip()
        scope = str(raw.get("scope", "both")).strip().lower() or "both"

        def _handler(args: dict[str, Any], ctx: dict[str, Any], skill_data: dict[str, Any] = raw) -> str:
            return _run_skill(skill_data, args, ctx)

        tools.append(
            ToolSpec(
                name=tool_name,
                description=(
                    f"Apply internal skill '{name}'. "
                    f"{description}" + (f" Scope: {scope}." if scope in {"queen", "worker", "both"} else "")
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Optional task context to pair with the skill guidance.",
                        },
                        "input": {
                            "type": "object",
                            "description": "Optional structured input context for this skill run.",
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Max characters to return from SKILL.md (200-200000).",
                        },
                    },
                    "additionalProperties": False,
                },
                permission="skill_use",
                handler=_handler,
            )
        )
    return tools


def _tool_list_skills(args: dict[str, Any], ctx: dict[str, Any]) -> str:
    workspace_dir = _workspace_root()
    include_disabled = bool(args.get("include_disabled", False))
    listed: list[dict[str, Any]] = []
    for raw in _load_skill_inventory(workspace_dir):
        enabled = bool(raw.get("enabled", True))
        if not include_disabled and not enabled:
            continue
        listed.append(
            {
                "id": str(raw.get("id", "")),
                "name": str(raw.get("name", "")),
                "description": str(raw.get("description", "")),
                "path": str(raw.get("path", "")),
                "scope": str(raw.get("scope", "both")),
                "enabled": enabled,
                "exists": bool(raw.get("exists", False)),
                "source": str(raw.get("source", "registry")),
                "auto_discovered": bool(raw.get("auto_discovered", False)),
            }
        )
    payload = {
        "count": len(listed),
        "registry_path": str(_registry_path(workspace_dir)),
        "skills": listed,
    }
    return json.dumps(payload, ensure_ascii=False)


def _tool_add_skill(args: dict[str, Any], ctx: dict[str, Any]) -> str:
    workspace_dir = _workspace_root()
    path_raw = str(args.get("path", "")).strip()
    scope = str(args.get("scope", "both")).strip().lower() or "both"
    enabled = bool(args.get("enabled", True))

    if not path_raw:
        return "add_skill error: path is required."
    if scope not in {"queen", "worker", "both"}:
        return "add_skill error: scope must be one of queen, worker, both."

    resolved_skill = _resolve_skill_file(workspace_dir, path_raw)
    if resolved_skill is None:
        return "add_skill error: skill path not found, invalid, or outside workspace."

    candidate_entry = {
        "id": str(args.get("id", "")).strip(),
        "name": str(args.get("name", "")).strip(),
        "description": str(args.get("description", "")).strip(),
        "scope": scope,
        "enabled": enabled,
        "path": resolved_skill.relative_to(workspace_dir).as_posix(),
    }
    bundle = load_skill_bundle(resolved_skill, workspace_dir=workspace_dir, registry_entry=candidate_entry)
    if bundle is None:
        return "add_skill error: SKILL.md is invalid or incomplete. Name/description may be missing."

    skill_id = bundle.id
    if not _SKILL_ID_RE.fullmatch(skill_id):
        return "add_skill error: id must match ^[a-z0-9][a-z0-9_-]*$."

    registry = _load_registry(workspace_dir)
    skills = [item for item in registry.get("skills", []) if isinstance(item, dict)]
    existing_idx = next((i for i, item in enumerate(skills) if str(item.get("id", "")) == skill_id), None)
    record = {
        "id": bundle.id,
        "name": bundle.name,
        "description": bundle.description,
        "path": bundle.skill_file.relative_to(workspace_dir).as_posix(),
        "scope": bundle.scope,
        "enabled": bundle.enabled,
    }
    if existing_idx is None:
        skills.append(record)
        action = "added"
    else:
        skills[existing_idx] = record
        action = "updated"

    registry["skills"] = skills
    _write_registry(workspace_dir, registry)

    return json.dumps(
        {
            "status": action,
            "id": skill_id,
            "path": record["path"],
            "registry_path": str(_registry_path(workspace_dir)),
            "message": f"Skill '{skill_id}' {action} successfully.",
        },
        ensure_ascii=False,
    )


def _tool_remove_skill(args: dict[str, Any], ctx: dict[str, Any]) -> str:
    workspace_dir = _workspace_root()
    skill_id = str(args.get("id", "")).strip()
    if not _SKILL_ID_RE.fullmatch(skill_id):
        return "remove_skill error: id must match ^[a-z0-9][a-z0-9_-]*$."

    registry = _load_registry(workspace_dir)
    skills = [item for item in registry.get("skills", []) if isinstance(item, dict)]
    kept = [item for item in skills if str(item.get("id", "")) != skill_id]
    if len(kept) == len(skills):
        return f"remove_skill error: skill '{skill_id}' not found."

    registry["skills"] = kept
    _write_registry(workspace_dir, registry)
    return json.dumps(
        {
            "status": "removed",
            "id": skill_id,
            "registry_path": str(_registry_path(workspace_dir)),
            "message": f"Skill '{skill_id}' removed from registry.",
        },
        ensure_ascii=False,
    )


def _run_skill(skill_data: dict[str, Any], args: dict[str, Any], ctx: dict[str, Any]) -> str:
    workspace_dir = _workspace_root()
    scope = str(skill_data.get("scope", "both")).strip().lower() or "both"
    caller_scope = _caller_scope(ctx)
    if scope == "queen" and caller_scope == "worker":
        return "skill error: this skill is scoped to queen only."
    if scope == "worker" and caller_scope == "queen":
        return "skill error: this skill is scoped to worker only."

    skill_path = _resolve_registered_skill_path(workspace_dir, skill_data)
    if skill_path is None or not skill_path.exists():
        return f"skill error: missing SKILL.md for '{skill_data.get('id', '<unknown>')}'."

    max_chars = _bounded_int(args.get("max_chars"), default=_DEFAULT_MAX_CHARS, low=200, high=_MAX_CHARS_LIMIT)
    task = str(args.get("task", "")).strip()
    input_payload = args.get("input")

    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"skill error: failed to read SKILL.md: {exc}"

    truncated = False
    if len(content) > max_chars:
        content = content[:max_chars]
        truncated = True

    payload = {
        "skill_id": str(skill_data.get("id", "")),
        "name": str(skill_data.get("name", "")),
        "description": str(skill_data.get("description", "")),
        "scope": scope,
        "path": str(skill_data.get("path", "")),
        "source": str(skill_data.get("source", "registry")),
        "task": task,
        "input": input_payload if isinstance(input_payload, (dict, list, str, int, float, bool)) else None,
        "truncated": truncated,
        "guidance": content,
    }
    return json.dumps(payload, ensure_ascii=False)


def _caller_scope(ctx: dict[str, Any]) -> str:
    if "queen" in ctx:
        return "queen"
    if "worker" in ctx:
        return "worker"
    return "unknown"


def _workspace_root() -> Path:
    raw = os.getenv("BROODMIND_WORKSPACE_DIR", "").strip()
    if raw:
        return Path(raw).resolve()
    cwd = Path.cwd().resolve()
    if cwd.name == "workers":
        return cwd.parent
    if cwd.parent.name == "workers":
        return cwd.parent.parent
    if (cwd / "workers").exists():
        return cwd
    default_candidate = Path("workspace").resolve()
    if (default_candidate / "workers").exists():
        return default_candidate
    return default_candidate


def _registry_path(workspace_dir: Path) -> Path:
    return workspace_dir / "skills" / "registry.json"


def _load_registry(workspace_dir: Path) -> dict[str, Any]:
    path = ensure_skills_layout(workspace_dir)
    if not path.exists():
        return {"version": _REGISTRY_VERSION, "skills": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse skills registry, using empty registry", path=str(path), error=str(exc))
        return {"version": _REGISTRY_VERSION, "skills": []}
    if not isinstance(payload, dict):
        return {"version": _REGISTRY_VERSION, "skills": []}
    skills = payload.get("skills")
    if not isinstance(skills, list):
        payload["skills"] = []
    payload.setdefault("version", _REGISTRY_VERSION)
    return payload


def _write_registry(workspace_dir: Path, payload: dict[str, Any]) -> None:
    path = _registry_path(workspace_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        tmp.replace(path)
    except PermissionError:
        # Windows can transiently deny os.replace when target is locked.
        path.write_text(text, encoding="utf-8")
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def _resolve_skill_file(workspace_dir: Path, path_raw: str) -> Path | None:
    candidate = Path(path_raw)
    if not candidate.is_absolute():
        candidate = workspace_dir / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(workspace_dir)
    except ValueError:
        return None
    if candidate.is_dir():
        preferred = candidate / "SKILL.md"
        fallback = candidate / "skill.md"
        if preferred.exists():
            candidate = preferred
        elif fallback.exists():
            candidate = fallback
        else:
            candidate = preferred
    if candidate.name.lower() != "skill.md":
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate


def _resolve_registered_skill_path(workspace_dir: Path, skill_data: dict[str, Any]) -> Path | None:
    raw = str(skill_data.get("path", "")).strip()
    if not raw:
        return None
    return _resolve_skill_file(workspace_dir, raw)


def _skill_path_exists(workspace_dir: Path, skill_data: dict[str, Any]) -> bool:
    return _resolve_registered_skill_path(workspace_dir, skill_data) is not None


def _load_skill_inventory(workspace_dir: Path) -> list[dict[str, Any]]:
    registry = _load_registry(workspace_dir)
    registry_skills = [item for item in registry.get("skills", []) if isinstance(item, dict)]
    inventory_by_id: dict[str, dict[str, Any]] = {}

    for raw in registry_skills:
        bundle = _load_registry_bundle(workspace_dir, raw)
        skill_id = str(raw.get("id", "")).strip()
        if bundle is not None:
            inventory_by_id[bundle.id] = _skill_record_from_bundle(
                workspace_dir,
                bundle,
                source="registry",
                auto_discovered=False,
            )
            continue
        if not _SKILL_ID_RE.fullmatch(skill_id):
            continue
        inventory_by_id[skill_id] = _skill_record_from_registry(workspace_dir, raw)

    for bundle_dir in discover_skill_bundle_dirs(workspace_dir):
        bundle = load_skill_bundle(bundle_dir, workspace_dir=workspace_dir)
        if bundle is None or bundle.id in inventory_by_id:
            continue
        inventory_by_id[bundle.id] = _skill_record_from_bundle(
            workspace_dir,
            bundle,
            source="bundle",
            auto_discovered=True,
        )

    return sorted(inventory_by_id.values(), key=lambda item: str(item.get("id", "")))


def _load_registry_bundle(workspace_dir: Path, raw: dict[str, Any]) -> SkillBundle | None:
    resolved = _resolve_registered_skill_path(workspace_dir, raw)
    if resolved is None:
        return None
    return load_skill_bundle(resolved, workspace_dir=workspace_dir, registry_entry=raw)


def _skill_record_from_bundle(
    workspace_dir: Path,
    bundle: SkillBundle,
    *,
    source: str,
    auto_discovered: bool,
) -> dict[str, Any]:
    return {
        "id": bundle.id,
        "name": bundle.name,
        "description": bundle.description,
        "path": bundle.skill_file.relative_to(workspace_dir).as_posix(),
        "scope": bundle.scope,
        "enabled": bundle.enabled,
        "exists": True,
        "source": source,
        "auto_discovered": auto_discovered,
        "bundle_dir": str(bundle.bundle_dir),
        "scripts_dir": str(bundle.scripts_dir) if bundle.scripts_dir else "",
        "references_dir": str(bundle.references_dir) if bundle.references_dir else "",
        "assets_dir": str(bundle.assets_dir) if bundle.assets_dir else "",
        "registry_path": bundle.registry_path or "",
    }


def _skill_record_from_registry(workspace_dir: Path, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw.get("id", "")).strip(),
        "name": str(raw.get("name", "")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "path": str(raw.get("path", "")).strip(),
        "scope": _resolve_scope_value(raw.get("scope")),
        "enabled": bool(raw.get("enabled", True)),
        "exists": _skill_path_exists(workspace_dir, raw),
        "source": "registry",
        "auto_discovered": False,
        "bundle_dir": "",
        "scripts_dir": "",
        "references_dir": "",
        "assets_dir": "",
        "registry_path": str(raw.get("path", "")).strip(),
    }


def _resolve_scope_value(value: Any) -> str:
    scope = str(value or "both").strip().lower() or "both"
    return scope if scope in {"queen", "worker", "both"} else "both"


def _slugify(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9_-]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _bounded_int(value: Any, *, default: int, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(low, min(high, parsed))
