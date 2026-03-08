# Repository Guidelines

## Project Structure & Module Organization

- `src/broodmind/` contains the main Python package: CLI, channels, gateway, memory, policy, providers, Queen runtime, scheduler, WhatsApp/Telegram integrations, workers, and shared utilities.
- `webapp/` holds the Vite-based dashboard frontend. `src/` contains app code and `dist/` contains built assets.
- `tests/` contains the pytest suite for CLI, dashboard, runtime, worker orchestration, memory, and channel behavior.
- `scripts/` contains setup and maintenance helpers such as bootstrap and worker-template sync utilities.
- `docker/` contains container assets, including the worker image Dockerfile.
- `data/` is runtime state storage for SQLite, metrics, auth state, and logs; avoid committing generated contents.
- `workspace/` is the default Queen/worker workspace and scratch area.
- `workspace_templates/` contains bootstrap content copied into new workspaces.
- `docs/` stores additional project documentation.

## Build, Test, and Development Commands

- `uv sync` installs the project and dev dependencies for day-to-day development.
- `python -m venv .venv` and `pip install -e .[dev]` are the non-`uv` editable setup path.
- `uv run broodmind configure` runs the interactive configuration wizard and bootstraps missing workspace files.
- `uv run broodmind start` starts BroodMind in background mode.
- `uv run broodmind start --foreground` runs the Queen and gateway in the foreground.
- `uv run broodmind stop`, `uv run broodmind restart`, and `uv run broodmind status` manage the local runtime.
- `uv run broodmind logs --follow` tails `data/logs/broodmind.log`.
- `uv run broodmind gateway` starts the FastAPI gateway directly.
- `uv run broodmind dashboard --once` prints one dashboard snapshot; `uv run broodmind dashboard --watch` runs the live terminal dashboard.
- `uv run broodmind sync-worker-templates --overwrite` refreshes default worker templates into `workspace/workers`.
- `uv run broodmind memory stats` and `uv run broodmind memory cleanup --dry-run` cover common memory maintenance flows.
- `uv run broodmind whatsapp install-bridge`, `uv run broodmind whatsapp link`, and `uv run broodmind whatsapp status` manage the WhatsApp bridge.
- `uv run broodmind build-worker-image --tag broodmind-worker:latest` builds the Docker worker image.
- `uv run pytest` runs the test suite.
- `uv run ruff check .`, `uv run black --check .`, and `uv run mypy src` are the configured lint/format/type-check commands.
- `npm install` and `npm run build` from `webapp/` build the dashboard bundle manually when needed.

## Coding Style & Naming Conventions

- Python code lives under `src/` with imports rooted at `broodmind`.
- Use 4-space indentation, type hints on new or changed Python code, and descriptive module names.
- Follow the configured tooling in `pyproject.toml`: Black for formatting, Ruff for linting/import order, and MyPy for type checks.
- Keep CLI entrypoints in `src/broodmind/cli/` and group related runtime code under focused packages such as `gateway/`, `memory/`, `queen/`, and `workers/`.
- Frontend code in `webapp/src/` should stay TypeScript-first and match the existing Vite/Tailwind setup.

## Testing Guidelines

- Add Python tests under `tests/` using `test_<module>.py` naming.
- Prefer focused pytest coverage near the behavior you change, especially for CLI flows, runtime safety checks, worker orchestration, and dashboard APIs.
- Run `uv run pytest` before finishing substantial changes. For frontend-only changes, also run `npm run build` in `webapp/`.
- When you add new tooling or test workflows, update this file and `README.md`.

## Commit & Pull Request Guidelines

- Use concise, imperative commit subjects such as `update AGENTS guide` or `harden worker status recovery`.
- Keep commits scoped to one logical change when practical.
- PRs should include a short description, linked issue if relevant, and logs or screenshots for user-facing CLI/dashboard changes.

## Security & Configuration Tips

- Copy `.env.example` to `.env` and keep secrets out of version control.
- Important settings include channel credentials, provider API keys, dashboard protection, and `BROODMIND_STATE_DIR` / workspace paths.
- Treat `data/`, WhatsApp auth state, and generated workspace files as local runtime artifacts unless the repo explicitly needs fixtures.

## Queen Context Reset Policy

- The Queen can invoke `queen_context_reset` to compact or reset overloaded chat context.
- Preferred default is `mode=soft` with structured handoff fields: `goal_now`, `done`, `open_threads`, `critical_constraints`, and `next_step`.
- Persist reset artifacts in workspace memory:
  - `memory/handoff.md`, `memory/handoff.json`
  - `memory/context-audit.md`, `memory/context-audit.jsonl`
- Confirmation is required when:
  - `mode=hard`
  - `confidence < 0.7`
  - repeated resets occur without progress (`N=2`)
- After reset, force a wake-up choice (`continue / clarify / replan`) before major actions.
