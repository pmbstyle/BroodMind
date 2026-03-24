from __future__ import annotations

from octopal.infrastructure.config.settings import load_settings
from octopal.gateway.app import build_app

settings = load_settings()
app = build_app(settings)
