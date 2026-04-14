from __future__ import annotations

from typer.testing import CliRunner

from octopal.cli.main import app

runner = CliRunner()


def test_update_rejects_dirty_git_checkout(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("octopal.cli.main._project_root", lambda: tmp_path)
    monkeypatch.setattr("octopal.cli.main._git_checkout_ready_for_update", lambda _root: (False, "dirty tree"))

    result = runner.invoke(app, ["update"])

    assert result.exit_code == 1
    assert "Update unavailable:" in result.stdout
    assert "dirty tree" in result.stdout


def test_update_runs_git_pull_and_uv_sync(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("octopal.cli.main._project_root", lambda: tmp_path)
    monkeypatch.setattr("octopal.cli.main._git_checkout_ready_for_update", lambda _root: (True, None))
    monkeypatch.setattr("octopal.cli.main.list_octopal_runtime_pids", lambda: [])
    monkeypatch.setattr(
        "octopal.cli.main._perform_git_update",
        lambda _root: (True, "Already up to date."),
    )

    result = runner.invoke(app, ["update"])

    assert result.exit_code == 0
    assert "Octopal updated." in result.stdout
    assert "Already up to date." in result.stdout
    assert "uv run octopal start" in result.stdout


def test_update_warns_when_runtime_is_active(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("octopal.cli.main._project_root", lambda: tmp_path)
    monkeypatch.setattr("octopal.cli.main._git_checkout_ready_for_update", lambda _root: (True, None))
    monkeypatch.setattr("octopal.cli.main.list_octopal_runtime_pids", lambda: [12345])
    monkeypatch.setattr(
        "octopal.cli.main._perform_git_update",
        lambda _root: (True, "Updating abc..def"),
    )

    result = runner.invoke(app, ["update"])

    assert result.exit_code == 0
    assert "Octopal is running right now." in result.stdout
    assert "uv run octopal restart" in result.stdout
