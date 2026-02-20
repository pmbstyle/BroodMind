# Telegram Bot Features

This document describes the Telegram UX features currently implemented in BroodMind.

## Commands

The bot now supports explicit slash commands:

- `/help`
  - Shows available bot commands.
- `/status`
  - Shows bot/runtime status, PID, last heartbeat, and active/recent worker count.
- `/workers`
  - Shows discovered worker templates and recent workers.
- `/memory [limit]`
  - Shows a memory snapshot summary (total entries, unique chats, role distribution).
  - Optional `limit` is clamped to `50..1000` (default `300`).
- `/version`
  - Shows the current bot version.

If a message is not a slash command, it follows the normal Queen message flow.

## Silent Memory Mode

You can log facts, notes, or observations to the Queen's memory without triggering a full conversation turn.

- **Prefix:** Start your message with `! ` or `> ` (e.g., `! The server IP is 10.0.0.5`).
- **Behavior:** The bot will react with a "✍️" (writing hand) emoji to confirm the note is saved. It will **not** generate a text reply.

## Image Support

The Queen can "see" images sent to the chat.

- **Usage:** Send a photo (with or without a caption).
- **Behavior:** The image is passed to the underlying vision-capable LLM for analysis. You can ask questions about the image or use it as context for a task.

## Reactions

The Queen can react to your messages with emojis to provide immediate feedback or express "emotion."

- **Behavior:** The Queen may react with emojis (like 👍, ❤️, 🤔) in addition to or instead of a text reply, depending on the context of the conversation.

## Progress Updates

The Queen emits progress milestones for worker launches and execution:

- `queued`
- `running`
- `completed`
- `failed`
- `duplicate`
- `worker_started`

Telegram receives these as lightweight progress messages. Repeated progress states are coalesced per chat for a short interval to reduce spam.

## Inline Worker Controls

When a worker starts, Telegram posts a control panel with inline buttons:

- `Refresh`
  - Fetches and shows the latest worker status.
- `Get result`
  - Fetches completed/failed result details.
- `Stop`
  - Stops a running worker.

## Callback Guardrails

Worker callback actions include safety checks:

- Callback payload format validation.
- Worker ID regex validation.
- Lock-safe execution under per-chat lock.
- Graceful handling for stale/cleaned-up workers (shows alert and removes outdated controls).
- State-aware controls: `Stop` is disabled when worker is no longer running.

## Notes

- All bot responses still use the existing queued sender path for ordered delivery.
- Existing approval callbacks (`approve:*`, `deny:*`) remain supported.
