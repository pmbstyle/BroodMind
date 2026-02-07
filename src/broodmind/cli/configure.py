from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from broodmind.cli.branding import print_banner
from broodmind.config.manager import ConfigManager

console = Console()

DEFAULT_AGENTS_MD = """# AGENTS.md - Workspace Operating Guide

This file defines how the Queen and workers should operate in this workspace.

## Core Roles

- **Queen**: plans, reasons, delegates, verifies, and reports.
- **Workers**: specialized executors for bounded tasks.
- **Worker templates**: reusable worker definitions in `workspace/workers/<id>/worker.json`.

## Runtime Memory

You wake up fresh each session. Persist important continuity to files:

- **Daily notes**: `memory/YYYY-MM-DD.md`
- **Long-term summary**: `MEMORY.md`
- **Canonical memory**: `memory/canon/facts.md`, `memory/canon/decisions.md`, `memory/canon/failures.md`

If you need to remember something, write it down.

## Required Bootstrap Files

- `AGENTS.md` (this file): operating instructions
- `USER.md`: user preferences and identity context
- `SOUL.md`: persona/style context
- `HEARTBEAT.md`: optional scheduled checks and proactive tasks
- `MEMORY.md`: long-term notes

## Worker Usage Rules

1. Use workers for scoped execution, not as a replacement for verification.
2. Prefer small, testable tasks with clear acceptance criteria.
3. After worker completion, record key outcomes in daily memory.
4. On worker failure, capture cause and mitigation in memory/canon when relevant.

## Safety Rules

1. Do not exfiltrate private data.
2. Do not perform destructive actions without explicit confirmation.
3. For external side effects (messages, posts, emails, deployments), confirm intent when uncertain.
4. Validate file paths and commands before execution.

## Heartbeat Behavior

Default heartbeat trigger instruction:

`Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.`

If no actionable heartbeat items exist, return `HEARTBEAT_OK`.
"""

DEFAULT_MEMORY_MD = """# MEMORY

Long-term memory for durable project context, decisions, and reminders.
"""


def configure_wizard() -> None:
    """Run the interactive configuration wizard."""
    print_banner()

    console.print(Panel(
        Text("Welcome to the BroodMind Configuration Wizard!\n", style="bold green") +
        Text("This tool will help you set up your environment to run the BroodMind Queen and Workers.", style="dim"),
        title="[bold cyan]Onboarding[/bold cyan]",
        border_style="blue",
        padding=(1, 2)
    ))

    config = ConfigManager()

    # 1. Telegram Bot Token
    console.print("\n[bold]Step 1: Telegram Integration[/bold]")
    console.print("You need a Telegram Bot Token from @BotFather.")
    current_token = config.get("TELEGRAM_BOT_TOKEN", "")
    token = Prompt.ask(
        "Enter your Telegram Bot Token",
        default=current_token,
        password=bool(current_token)
    )
    if token:
        config.set("TELEGRAM_BOT_TOKEN", token)

    # 2. Allowed Chat IDs
    console.print("\n[bold]Step 2: Access Control[/bold]")
    console.print("Which Telegram users/groups are allowed to talk to the Queen?")
    console.print("[dim]You can find your ID by messaging @userinfobot on Telegram.[/dim]")
    current_ids = config.get("ALLOWED_TELEGRAM_CHAT_IDS", "")
    allowed_ids = Prompt.ask(
        "Enter allowed Chat IDs (comma-separated)",
        default=current_ids
    )
    if allowed_ids:
        config.set("ALLOWED_TELEGRAM_CHAT_IDS", allowed_ids)

    # 3. LLM Provider
    console.print("\n[bold]Step 3: LLM Provider[/bold]")
    current_provider = config.get("BROODMIND_LLM_PROVIDER", "litellm")
    provider = Prompt.ask(
        "Choose LLM Provider",
        choices=["litellm", "openrouter"],
        default=current_provider
    )
    config.set("BROODMIND_LLM_PROVIDER", provider)

    if provider == "openrouter":
        console.print("\n[bold]Step 3a: OpenRouter Configuration[/bold]")
        current_or_key = config.get("OPENROUTER_API_KEY", "")
        or_key = Prompt.ask(
            "Enter OpenRouter API Key",
            default=current_or_key,
            password=bool(current_or_key)
        )
        if or_key:
            config.set("OPENROUTER_API_KEY", or_key)

        current_or_model = config.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        or_model = Prompt.ask("Enter default OpenRouter model", default=current_or_model)
        config.set("OPENROUTER_MODEL", or_model)
    else:
        console.print("\n[bold]Step 3a: LiteLLM / Z.ai Configuration[/bold]")
        current_zai_key = config.get("ZAI_API_KEY", "")
        zai_key = Prompt.ask(
            "Enter Z.ai (or OpenAI-compatible) API Key",
            default=current_zai_key,
            password=bool(current_zai_key)
        )
        if zai_key:
            config.set("ZAI_API_KEY", zai_key)

        current_zai_model = config.get("ZAI_MODEL", "glm-4.7")
        zai_model = Prompt.ask("Enter default model name", default=current_zai_model)
        config.set("ZAI_MODEL", zai_model)

    # 4. Workspace and State
    console.print("\n[bold]Step 4: Storage[/bold]")
    current_workspace = config.get("BROODMIND_WORKSPACE_DIR", "workspace")
    workspace = Prompt.ask("Enter workspace directory path", default=current_workspace)
    config.set("BROODMIND_WORKSPACE_DIR", workspace)
    workspace_result = _ensure_workspace_markdown_files(Path(workspace))

    current_state = config.get("BROODMIND_STATE_DIR", "data")
    state_dir = Prompt.ask("Enter state directory (DB, logs)", default=current_state)
    config.set("BROODMIND_STATE_DIR", state_dir)

    # 5. Optional Features
    console.print("\n[bold]Step 5: Optional Features[/bold]")

    # Brave Search
    if Confirm.ask("Do you want to enable Web Search (requires Brave API key)?", default=False):
        current_brave = config.get("BRAVE_API_KEY", "")
        brave_key = Prompt.ask("Enter Brave API Key", default=current_brave)
        if brave_key:
            config.set("BRAVE_API_KEY", brave_key)

    # OpenAI Embeddings
    if Confirm.ask("Do you want to enable Semantic Memory (requires OpenAI API key)?", default=False):
        current_openai = config.get("OPENAI_API_KEY", "")
        openai_key = Prompt.ask("Enter OpenAI API Key", default=current_openai)
        if openai_key:
            config.set("OPENAI_API_KEY", openai_key)

    console.print()
    if workspace_result["created"]:
        created_lines = "\n".join(f"- {path}" for path in workspace_result["created"])
    else:
        created_lines = "- none (all files already existed)"

    console.print(Panel(
        "[bold cyan]Workspace bootstrap complete[/bold cyan]\n"
        f"Created files:\n{created_lines}",
        border_style="blue"
    ))

    console.print(Panel(
        "[bold green][V] Configuration complete![/bold green]\n"
        f"Settings saved to: [cyan]{config.env_path.absolute()}[/cyan]\n\n"
        "You can now start the BroodMind Queen with:\n"
        "[bold magenta]broodmind start[/bold magenta]",
        border_style="green"
    ))


def _ensure_workspace_markdown_files(workspace_dir: Path) -> dict[str, list[str]]:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    canon_dir = workspace_dir / "memory" / "canon"
    canon_dir.mkdir(parents=True, exist_ok=True)

    file_specs: dict[Path, str] = {
        workspace_dir / "AGENTS.md": DEFAULT_AGENTS_MD,
        workspace_dir / "MEMORY.md": DEFAULT_MEMORY_MD,
        workspace_dir / "SOUL.md": "",
        workspace_dir / "USER.md": "",
        workspace_dir / "HEARTBEAT.md": "",
        canon_dir / "facts.md": "# Facts\n\n",
        canon_dir / "decisions.md": "# Decisions\n\n",
        canon_dir / "failures.md": "# Failures\n\n",
    }

    created: list[str] = []
    for path, content in file_specs.items():
        if path.exists():
            continue
        path.write_text(content, encoding="utf-8")
        created.append(str(path.relative_to(workspace_dir).as_posix()))

    return {"created": created}
