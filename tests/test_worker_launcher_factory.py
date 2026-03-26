from __future__ import annotations

from pathlib import Path

from octopal.infrastructure.config.models import WorkerRuntimeConfig
from octopal.infrastructure.config.settings import Settings
from octopal.runtime.workers.launcher import DockerLauncher, SameEnvLauncher
from octopal.runtime.workers.launcher_factory import build_launcher, detect_docker_cli


def test_worker_runtime_config_defaults_to_docker() -> None:
    config = WorkerRuntimeConfig()
    assert config.launcher == "docker"


def test_settings_default_worker_launcher_is_docker() -> None:
    settings = Settings()
    assert settings.worker_launcher == "docker"


def test_detect_docker_cli_reports_missing_when_not_on_path(monkeypatch) -> None:
    monkeypatch.setattr("octopal.runtime.workers.launcher_factory.shutil.which", lambda name: None)
    ok, detail = detect_docker_cli()
    assert ok is False
    assert "not found" in detail.lower()


def test_build_launcher_returns_docker_launcher_when_cli_is_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("octopal.runtime.workers.launcher_factory.shutil.which", lambda name: "/usr/bin/docker")
    settings = Settings(
        OCTOPAL_WORKSPACE_DIR=tmp_path / "workspace",
        OCTOPAL_WORKER_LAUNCHER="docker",
    )

    launcher = build_launcher(settings)
    assert isinstance(launcher, DockerLauncher)


def test_build_launcher_falls_back_to_same_env_when_docker_cli_is_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("octopal.runtime.workers.launcher_factory.shutil.which", lambda name: None)
    settings = Settings(
        OCTOPAL_WORKSPACE_DIR=tmp_path / "workspace",
        OCTOPAL_WORKER_LAUNCHER="docker",
    )

    launcher = build_launcher(settings)
    assert isinstance(launcher, SameEnvLauncher)
