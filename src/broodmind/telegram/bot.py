from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher

from broodmind.config.settings import Settings
from broodmind.memory.service import MemoryService
from broodmind.policy.engine import PolicyEngine
from broodmind.providers.openai_embeddings import OpenAIEmbeddingsProvider
from broodmind.providers.litellm_provider import LiteLLMProvider
from broodmind.queen.core import Queen
from broodmind.store.sqlite import SQLiteStore
from broodmind.telegram.approvals import ApprovalManager
from broodmind.telegram.handlers import register_handlers
from broodmind.workers.launcher_factory import build_launcher
from broodmind.workers.runtime import WorkerRuntime

logger = logging.getLogger(__name__)


def build_dispatcher(settings: Settings, bot: Bot) -> Dispatcher:
    provider = LiteLLMProvider(settings)
    store = SQLiteStore(settings)

    # Initialize default worker templates
    from broodmind.workers.templates import initialize_templates
    initialize_templates(store)

    policy = PolicyEngine()
    launcher = build_launcher(settings)
    runtime = WorkerRuntime(
        store=store,
        policy=policy,
        workspace_dir=settings.workspace_dir,
        launcher=launcher,
    )
    approvals = ApprovalManager(bot=bot)
    embeddings = None
    if settings.openai_api_key:
        embeddings = OpenAIEmbeddingsProvider(settings)
    memory = MemoryService(
        store=store,
        embeddings=embeddings,
        top_k=settings.memory_top_k,
        min_score=settings.memory_min_score,
        max_chars=settings.memory_max_chars,
    )
    queen = Queen(
        provider=provider,
        store=store,
        policy=policy,
        runtime=runtime,
        approvals=approvals,
        memory=memory,
    )

    dp = Dispatcher()
    register_handlers(dp, queen, approvals, settings, bot)
    return dp, queen


async def run_bot(settings: Settings) -> None:
    bot = Bot(token=settings.telegram_bot_token)
    dp, queen = build_dispatcher(settings, bot)

    # Parse allowed chat IDs from settings
    allowed_chat_ids = []
    if settings.allowed_telegram_chat_ids:
        try:
            allowed_chat_ids = [
                int(cid.strip()) for cid in settings.allowed_telegram_chat_ids.split(",") if cid.strip()
            ]
        except ValueError:
            logger.error("Invalid ALLOWED_TELEGRAM_CHAT_IDS format - must be comma-separated integers")

    # Initialize queen system before starting polling
    logger.info("Initializing queen system")
    await queen.initialize_system(bot, allowed_chat_ids=allowed_chat_ids)
    logger.info("Queen system initialization complete")

    logger.info("Starting Telegram polling")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
