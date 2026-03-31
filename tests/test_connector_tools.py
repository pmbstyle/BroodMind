from __future__ import annotations

import asyncio
import json

from octopal.infrastructure.config.models import ConnectorInstanceConfig, OctopalConfig
from octopal.infrastructure.connectors.manager import ConnectorManager
from octopal.tools.catalog import get_tools
from octopal.tools.connectors.status import connector_status_read


def test_catalog_includes_read_only_connector_status_tool() -> None:
    tools = get_tools(mcp_manager=None)
    names = {tool.name for tool in tools}

    assert "connector_status" in names


def test_connector_status_tool_reads_status_from_octo_context() -> None:
    config = OctopalConfig()
    config.connectors.instances["google"] = ConnectorInstanceConfig(
        enabled=True,
        enabled_services=["gmail"],
        credentials={"client_id": "client-id", "client_secret": "client-secret"},
    )
    manager = ConnectorManager(config=config.connectors, mcp_manager=None, octo_config=config)

    class _Octo:
        connector_manager = manager

    payload = asyncio.run(connector_status_read({}, {"octo": _Octo()}))
    data = json.loads(payload)

    assert data["connectors"]["google"]["status"] == "needs_auth"


def test_connector_status_tool_can_filter_to_single_connector() -> None:
    config = OctopalConfig()
    config.connectors.instances["google"] = ConnectorInstanceConfig(enabled=False)
    manager = ConnectorManager(config=config.connectors, mcp_manager=None, octo_config=config)

    class _Octo:
        connector_manager = manager

    payload = asyncio.run(connector_status_read({"name": "google"}, {"octo": _Octo()}))
    data = json.loads(payload)

    assert set(data["connectors"]) == {"google"}
    assert data["connectors"]["google"]["status"] == "disabled"
