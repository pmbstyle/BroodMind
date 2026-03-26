from __future__ import annotations

import shutil

import structlog

from octopal.infrastructure.config.settings import Settings
from octopal.runtime.workers.launcher import DockerLauncher, SameEnvLauncher, WorkerLauncher

logger = structlog.get_logger(__name__)


def detect_docker_cli() -> tuple[bool, str]:
    docker_path = shutil.which("docker")
    if not docker_path:
        return False, "Docker CLI was not found on PATH."
    return True, docker_path


def build_launcher(settings: Settings) -> WorkerLauncher:
    if settings.worker_launcher == "docker":
        docker_ok, docker_detail = detect_docker_cli()
        if not docker_ok:
            logger.warning(
                "Docker launcher requested but Docker CLI is unavailable; falling back to same_env",
                reason=docker_detail,
            )
            return SameEnvLauncher()
        host_workspace = settings.worker_docker_host_workspace
        if not host_workspace:
            host_workspace = str(settings.workspace_dir.resolve())
        return DockerLauncher(
            image=settings.worker_docker_image,
            host_workspace=host_workspace,
            container_workspace=settings.worker_docker_workspace,
        )
    return SameEnvLauncher()
