from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from broodmind.cli.branding import print_banner
from broodmind.config.manager import ConfigManager

console = Console()


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
    console.print(Panel(
        "[bold green][V] Configuration complete![/bold green]\n"
        f"Settings saved to: [cyan]{config.env_path.absolute()}[/cyan]\n\n"
        "You can now start the BroodMind Queen with:\n"
        "[bold magenta]broodmind start[/bold magenta]",
        border_style="green"
    ))
