from __future__ import annotations

import os
from fastapi import FastAPI
from octopal.infrastructure.config.settings import Settings
from octopal.gateway.dashboard import register_dashboard_routes
from octopal.gateway.ws import register_ws_routes
from octopal.runtime.queen.core import Queen
from octopal.tools.skills.management import ensure_skills_layout
from octopal.channels.whatsapp.routes import register_whatsapp_routes

def build_app(settings: Settings, queen: Queen | None = None) -> FastAPI:
    """Build the FastAPI app for the Octopal Gateway.
    
    It reuses the shared Queen instance for WebSocket communication.
    """
    os.environ.setdefault("OCTOPAL_STATE_DIR", str(settings.state_dir))
    os.environ.setdefault("OCTOPAL_WORKSPACE_DIR", str(settings.workspace_dir))
    ensure_skills_layout(settings.workspace_dir)
    app = FastAPI(title="Octopal Gateway")
    
    app.state.settings = settings
    app.state.queen = queen
    
    # Expose necessary components if any route needs them
    if queen:
        app.state.store = queen.store
        app.state.policy = queen.policy
        app.state.runtime = queen.runtime
        app.state.provider = queen.provider
        app.state.memory = queen.memory
        app.state.canon = queen.canon
    
    register_ws_routes(app)
    register_dashboard_routes(app)
    register_whatsapp_routes(app)
    return app
