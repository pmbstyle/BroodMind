from __future__ import annotations

from broodmind.tools.exec_run import exec_run
from broodmind.tools.filesystem import fs_delete, fs_list, fs_move, fs_read, fs_write
from broodmind.tools.registry import ToolSpec
from broodmind.tools.web_fetch import web_fetch
from broodmind.tools.web_search import web_search


def get_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="web_search",
            description="Search the web using Brave Search and return a JSON list of results (title, url, snippet).",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text."},
                    "count": {"type": "integer", "description": "Max results to return (1-10)."},
                    "country": {"type": "string", "description": "Country code for localization (e.g., US, CA)."},
                    "search_lang": {"type": "string", "description": "Search language (e.g., en)."},
                    "ui_lang": {"type": "string", "description": "UI language (e.g., en)."},
                    "freshness": {
                        "type": "string",
                        "description": "Time filter (e.g., 1d, 7d, 30d).",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            permission="network",
            handler=lambda args, ctx: web_search(args),
        ),
        ToolSpec(
            name="web_fetch",
            description="Fetch a URL and return a JSON payload with status_code, content_type, and snippet.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch (http/https only)."},
                    "max_chars": {
                        "type": "integer",
                        "description": "Max characters of content to return (200-200000).",
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
            permission="network",
            handler=lambda args, ctx: web_fetch(args),
        ),
        ToolSpec(
            name="fs_read",
            description="Read a file from the workspace. Returns file contents as text.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative path to read.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            permission="filesystem_read",
            handler=lambda args, ctx: fs_read(args, ctx["base_dir"]),
        ),
        ToolSpec(
            name="fs_write",
            description="Write a file to the workspace. Overwrites if the file exists.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative path to write.",
                    },
                    "content": {"type": "string", "description": "File contents."},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            permission="filesystem_write",
            handler=lambda args, ctx: fs_write(args, ctx["base_dir"]),
        ),
        ToolSpec(
            name="fs_list",
            description="List entries in a workspace directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative directory to list. Defaults to root.",
                    }
                },
                "additionalProperties": False,
            },
            permission="filesystem_read",
            handler=lambda args, ctx: fs_list(args, ctx["base_dir"]),
        ),
        ToolSpec(
            name="fs_move",
            description="Move or rename a file/directory.",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Workspace-relative source path.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Workspace-relative destination path.",
                    },
                },
                "required": ["source", "destination"],
                "additionalProperties": False,
            },
            permission="filesystem_write",
            handler=lambda args, ctx: fs_move(args, ctx["base_dir"]),
        ),
        ToolSpec(
            name="fs_delete",
            description="Delete a file or directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative path to delete.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            permission="filesystem_write",
            handler=lambda args, ctx: fs_delete(args, ctx["base_dir"]),
        ),
        ToolSpec(
            name="exec_run",
            description="Run a shell command in the workspace and return stdout/stderr.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute."},
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Timeout in seconds.",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            permission="exec",
            handler=lambda args, ctx: exec_run(args, ctx["base_dir"]),
        ),
    ]
