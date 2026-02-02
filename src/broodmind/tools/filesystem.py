from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any


def fs_read(args: dict[str, Any], base_dir: Path) -> str:
    path = str(args.get("path", "")).strip()
    if not path:
        return "fs_read error: path is required."
    target = (base_dir / path).resolve()
    if not _is_within(base_dir, target):
        return "fs_read error: path outside workspace."
    try:
        return target.read_text(encoding="utf-8")
    except Exception as exc:
        return f"fs_read error: {exc}"


def fs_write(args: dict[str, Any], base_dir: Path) -> str:
    path = str(args.get("path", "")).strip()
    content = str(args.get("content", ""))
    if not path:
        return "fs_write error: path is required."
    target = (base_dir / path).resolve()
    if not _is_within(base_dir, target):
        return "fs_write error: path outside workspace."
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return "fs_write ok"
    except Exception as exc:
        return f"fs_write error: {exc}"


def fs_list(args: dict[str, Any], base_dir: Path) -> str:
    path = str(args.get("path", "")).strip() or "."
    target = (base_dir / path).resolve()
    if not _is_within(base_dir, target):
        return "fs_list error: path outside workspace."
    if not target.exists():
        return "fs_list error: path does not exist."
    if not target.is_dir():
        return "fs_list error: path is not a directory."
    try:
        entries = sorted([p.name for p in target.iterdir()])
        return "\n".join(entries)
    except Exception as exc:
        return f"fs_list error: {exc}"


def fs_move(args: dict[str, Any], base_dir: Path) -> str:
    source = str(args.get("source", "")).strip()
    destination = str(args.get("destination", "")).strip()
    if not source or not destination:
        return "fs_move error: source and destination are required."
    src = (base_dir / source).resolve()
    dst = (base_dir / destination).resolve()
    if not _is_within(base_dir, src) or not _is_within(base_dir, dst):
        return "fs_move error: path outside workspace."
    if not src.exists():
        return "fs_move error: source does not exist."
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return "fs_move ok"
    except Exception as exc:
        return f"fs_move error: {exc}"


def fs_delete(args: dict[str, Any], base_dir: Path) -> str:
    path = str(args.get("path", "")).strip()
    if not path:
        return "fs_delete error: path is required."
    target = (base_dir / path).resolve()
    if not _is_within(base_dir, target):
        return "fs_delete error: path outside workspace."
    if not target.exists():
        return "fs_delete error: path does not exist."
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return "fs_delete ok"
    except Exception as exc:
        return f"fs_delete error: {exc}"


def _is_within(base_dir: Path, target: Path) -> bool:
    try:
        base = base_dir.resolve()
        return base == target or base in target.parents
    except Exception:
        return False
