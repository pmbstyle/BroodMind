from __future__ import annotations

import json
from types import SimpleNamespace

from octopal.runtime.state import (
    mark_runtime_running,
    resolve_runtime_status_display,
    write_start_status,
)


def test_write_start_status_persists_active_channel(tmp_path) -> None:
    settings = SimpleNamespace(state_dir=tmp_path, user_channel="whatsapp")
    write_start_status(settings)

    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["active_channel"] == "WhatsApp"
    assert payload["phase"] == "starting"


def test_mark_runtime_running_updates_phase(tmp_path) -> None:
    settings = SimpleNamespace(state_dir=tmp_path, user_channel="telegram")
    write_start_status(settings)

    mark_runtime_running(settings)

    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["phase"] == "running"


def test_resolve_runtime_status_display_uses_starting_phase() -> None:
    status_text, status_color = resolve_runtime_status_display(
        status_data={"phase": "starting"},
        pid_running=True,
    )
    assert status_text == "STARTING"
    assert status_color == "yellow"
