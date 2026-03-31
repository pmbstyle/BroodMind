from __future__ import annotations

import json
from typing import Any

import structlog

from octopal.infrastructure.connectors.base import Connector

logger = structlog.get_logger(__name__)

class GoogleConnector(Connector):
    def __init__(self, manager: Any):
        self.manager = manager
        self._service_scopes = {
            "gmail": "https://www.googleapis.com/auth/gmail.modify",
            "calendar": "https://www.googleapis.com/auth/calendar",
            "drive": "https://www.googleapis.com/auth/drive",
            "sheets": "https://www.googleapis.com/auth/spreadsheets",
            "docs": "https://www.googleapis.com/auth/documents",
        }

    @property
    def name(self) -> str:
        return "google"

    def _get_enabled_services(self) -> list[str]:
        config = self.manager.config.instances.get(self.name)
        if not config:
            return []
        return config.settings.get("enabled_services", ["gmail", "drive", "calendar", "sheets", "docs"])

    def _get_scopes(self) -> list[str]:
        enabled = self._get_enabled_services()
        return [self._service_scopes[svc] for svc in enabled if svc in self._service_scopes]

    async def get_status(self) -> dict[str, Any]:
        config = self.manager.config.instances.get(self.name)
        if not config or not config.enabled:
            return {"status": "disabled"}
        
        settings = config.settings
        enabled_services = self._get_enabled_services()
        
        if not settings.get("client_id") or not settings.get("client_secret"):
            return {
                "status": "not_configured", 
                "message": "Missing client_id or client_secret",
                "services": enabled_services
            }
        
        if not settings.get("refresh_token"):
            return {
                "status": "needs_auth", 
                "message": "Connector configured but needs user authorization",
                "services": enabled_services
            }
        
        return {
            "status": "ready", 
            "message": f"Google connector is ready with services: {', '.join(enabled_services)}",
            "services": enabled_services
        }

    async def configure(self, settings: dict[str, Any]) -> None:
        """Update settings for the Google connector."""
        config = self.manager.config.instances.get(self.name)
        if not config:
            from octopal.infrastructure.config.models import ConnectorInstanceConfig
            config = ConnectorInstanceConfig(enabled=True)
            self.manager.config.instances[self.name] = config
        
        # Merge settings
        config.settings.update(settings)
        config.enabled = True
        
        # Save config
        self.manager.save_config()

    async def setup(self) -> dict[str, Any]:
        """Start OAuth2 flow."""
        try:
            from google_auth_oauthlib.flow import Flow
        except ImportError:
            return {"error": "google-auth-oauthlib is not installed. Please install it to use the Google connector."}

        config = self.manager.config.instances.get(self.name)
        if not config:
            return {"error": "Google connector not configured. Call configure first."}
        
        settings = config.settings
        client_id = settings.get("client_id")
        client_secret = settings.get("client_secret")
        
        if not client_id or not client_secret:
            return {"error": "Missing client_id or client_secret in Google connector settings."}

        scopes = self._get_scopes()
        if not scopes:
            return {"error": "No Google services enabled. Please enable at least one service (gmail, drive, etc.) in configuration."}

        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob" # Out-of-band for CLI/Bot
        )

        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        
        return {
            "auth_url": auth_url,
            "message": f"Please visit the URL above to authorize Octo to access your Google services ({', '.join(self._get_enabled_services())}). After authorizing, you will receive a code. Provide this code to complete the setup."
        }

    async def complete_setup(self, data: dict[str, Any]) -> dict[str, Any]:
        """Complete OAuth2 flow with auth code."""
        try:
            from google_auth_oauthlib.flow import Flow
        except ImportError:
            return {"error": "google-auth-oauthlib is not installed."}

        auth_code = data.get("auth_code")
        if not auth_code:
            return {"error": "Missing auth_code."}

        config = self.manager.config.instances.get(self.name)
        settings = config.settings
        
        client_config = {
            "web": {
                "client_id": settings.get("client_id"),
                "client_secret": settings.get("client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=self._get_scopes(),
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )

        try:
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Store tokens
            settings["refresh_token"] = credentials.refresh_token
            settings["token"] = credentials.token
            
            # Save config
            self.manager.save_config()
            
            # Register MCP servers automatically
            await self._register_mcp_server()
            
            return {"status": "success", "message": f"Google connector setup complete for {', '.join(self._get_enabled_services())}."}
        except Exception as e:
            logger.exception("Failed to complete Google connector setup")
            return {"error": f"Failed to exchange code for tokens: {e}"}

    async def _register_mcp_server(self) -> None:
        """Register enabled Google MCP servers in mcp_servers.json."""
        config = self.manager.config.instances.get(self.name)
        settings = config.settings
        enabled_services = self._get_enabled_services()
        
        from octopal.infrastructure.mcp.manager import MCPServerConfig
        
        common_env = {
            "GOOGLE_CLIENT_ID": settings.get("client_id"),
            "GOOGLE_CLIENT_SECRET": settings.get("client_secret"),
            "GOOGLE_REFRESH_TOKEN": settings.get("refresh_token"),
        }

        # Google Drive / Docs / Sheets often use the same server
        if any(s in enabled_services for s in ["drive", "docs", "sheets"]):
            drive_cfg = MCPServerConfig(
                id="google-drive",
                name="Google Drive & Docs",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-google-drive"],
                env=common_env,
                transport="stdio"
            )
            await self.manager.mcp_manager.connect_server(drive_cfg)

        if "gmail" in enabled_services:
            gmail_cfg = MCPServerConfig(
                id="google-gmail",
                name="Gmail Connector",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-gmail"],
                env=common_env,
                transport="stdio"
            )
            await self.manager.mcp_manager.connect_server(gmail_cfg)
        
        # Note: Calendar might need its own MCP server if available, 
        # or it might be part of another one. For now we handle Gmail and Drive.
