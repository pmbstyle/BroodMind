from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx
from mcp.server import FastMCP

_GITHUB_API_BASE_URL = "https://api.github.com"
_DEFAULT_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GitHubConfigError(RuntimeError):
    """Raised when required GitHub MCP configuration is missing."""


class GitHubApiError(RuntimeError):
    """Raised when GitHub returns a structured error response."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.details = details or {}
        super().__init__(f"GitHub API {status_code}: {message}")


def _parse_github_api_error(response: httpx.Response) -> GitHubApiError:
    payload: dict[str, Any] = {}
    try:
        payload = response.json()
    except json.JSONDecodeError:
        text = response.text.strip() or response.reason_phrase
        return GitHubApiError(status_code=response.status_code, message=text, details={})

    message = str(payload.get("message") or response.reason_phrase or "Unknown GitHub API error").strip()
    return GitHubApiError(status_code=response.status_code, message=message, details=payload)


def _normalize_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(user, dict):
        return None
    return {
        "login": user.get("login"),
        "id": user.get("id"),
        "type": user.get("type"),
        "site_admin": user.get("site_admin", False),
        "html_url": user.get("html_url"),
    }


def _normalize_repo(repo: dict[str, Any]) -> dict[str, Any]:
    owner = _normalize_user(repo.get("owner"))
    return {
        "id": repo.get("id"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "private": repo.get("private", False),
        "default_branch": repo.get("default_branch"),
        "description": repo.get("description"),
        "html_url": repo.get("html_url"),
        "clone_url": repo.get("clone_url"),
        "ssh_url": repo.get("ssh_url"),
        "visibility": repo.get("visibility"),
        "language": repo.get("language"),
        "fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "disabled": repo.get("disabled", False),
        "open_issues_count": repo.get("open_issues_count"),
        "stargazers_count": repo.get("stargazers_count"),
        "watchers_count": repo.get("watchers_count"),
        "forks_count": repo.get("forks_count"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "owner": owner,
    }


def _normalize_issue(issue: dict[str, Any]) -> dict[str, Any]:
    assignees = issue.get("assignees") or []
    labels = issue.get("labels") or []
    return {
        "id": issue.get("id"),
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "state_reason": issue.get("state_reason"),
        "html_url": issue.get("html_url"),
        "comments": issue.get("comments"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
        "body": issue.get("body"),
        "user": _normalize_user(issue.get("user")),
        "assignees": [_normalize_user(assignee) for assignee in assignees],
        "labels": [
            {
                "name": label.get("name"),
                "color": label.get("color"),
                "description": label.get("description"),
            }
            for label in labels
            if isinstance(label, dict)
        ],
        "pull_request": issue.get("pull_request"),
    }


def _normalize_pull_request(pr: dict[str, Any]) -> dict[str, Any]:
    head = pr.get("head") or {}
    base = pr.get("base") or {}
    return {
        "id": pr.get("id"),
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "draft": pr.get("draft", False),
        "merged": pr.get("merged"),
        "mergeable": pr.get("mergeable"),
        "html_url": pr.get("html_url"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "closed_at": pr.get("closed_at"),
        "merged_at": pr.get("merged_at"),
        "body": pr.get("body"),
        "user": _normalize_user(pr.get("user")),
        "head": {
            "label": head.get("label"),
            "ref": head.get("ref"),
            "sha": head.get("sha"),
            "repo": _normalize_repo(head.get("repo")) if isinstance(head.get("repo"), dict) else None,
        },
        "base": {
            "label": base.get("label"),
            "ref": base.get("ref"),
            "sha": base.get("sha"),
            "repo": _normalize_repo(base.get("repo")) if isinstance(base.get("repo"), dict) else None,
        },
    }


class GitHubApiClient:
    def __init__(self) -> None:
        self._token = self._load_token()
        self._client = httpx.AsyncClient(base_url=_GITHUB_API_BASE_URL, timeout=30.0)

    def _load_token(self) -> str:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise GitHubConfigError("Missing GitHub MCP credentials. Expected GITHUB_TOKEN.")
        return token

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._client.request(
            method,
            path,
            params=params,
            headers={
                **_DEFAULT_HEADERS,
                "Authorization": f"Bearer {self._token}",
            },
        )
        if response.is_error:
            raise _parse_github_api_error(response)
        if not response.content:
            return {}
        return response.json()

    async def get_authenticated_user(self) -> dict[str, Any]:
        payload = await self._request("GET", "/user")
        return {
            "login": payload.get("login"),
            "id": payload.get("id"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "company": payload.get("company"),
            "html_url": payload.get("html_url"),
            "avatar_url": payload.get("avatar_url"),
        }

    async def list_repositories(
        self,
        *,
        visibility: str | None = None,
        affiliation: str | None = None,
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "sort": sort,
            "direction": direction,
            "per_page": max(1, min(per_page, 100)),
            "page": max(1, page),
        }
        if visibility:
            params["visibility"] = visibility
        if affiliation:
            params["affiliation"] = affiliation
        payload = await self._request("GET", "/user/repos", params=params)
        return {"repositories": [_normalize_repo(repo) for repo in payload]}

    async def get_repository(self, *, owner: str, repo: str) -> dict[str, Any]:
        payload = await self._request("GET", f"/repos/{owner}/{repo}")
        return _normalize_repo(payload)

    async def list_issues(
        self,
        *,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str | None = None,
        since: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "state": state,
            "per_page": max(1, min(per_page, 100)),
            "page": max(1, page),
        }
        if labels:
            params["labels"] = labels
        if since:
            params["since"] = since
        payload = await self._request("GET", f"/repos/{owner}/{repo}/issues", params=params)
        return {
            "owner": owner,
            "repo": repo,
            "issues": [_normalize_issue(issue) for issue in payload],
        }

    async def get_issue(self, *, owner: str, repo: str, issue_number: int) -> dict[str, Any]:
        payload = await self._request("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")
        return _normalize_issue(payload)

    async def list_pull_requests(
        self,
        *,
        owner: str,
        repo: str,
        state: str = "open",
        head: str | None = None,
        base: str | None = None,
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": max(1, min(per_page, 100)),
            "page": max(1, page),
        }
        if head:
            params["head"] = head
        if base:
            params["base"] = base
        payload = await self._request("GET", f"/repos/{owner}/{repo}/pulls", params=params)
        return {
            "owner": owner,
            "repo": repo,
            "pull_requests": [_normalize_pull_request(pr) for pr in payload],
        }

    async def get_pull_request(self, *, owner: str, repo: str, pull_number: int) -> dict[str, Any]:
        payload = await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")
        return _normalize_pull_request(payload)


mcp = FastMCP(
    name="Octopal GitHub",
    instructions=(
        "Use these tools to inspect the connected GitHub account, repositories, issues, and pull requests. "
        "Prefer list tools to discover repositories or PR numbers before fetching a single item."
    ),
    log_level="ERROR",
)

_github_client: GitHubApiClient | None = None


def _client() -> GitHubApiClient:
    global _github_client
    if _github_client is None:
        _github_client = GitHubApiClient()
    return _github_client


@mcp.tool(name="get_authenticated_user")
async def get_authenticated_user() -> dict[str, Any]:
    """Return basic information about the connected GitHub user."""
    return await _client().get_authenticated_user()


@mcp.tool(name="list_repositories")
async def list_repositories(
    visibility: str | None = None,
    affiliation: str | None = None,
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """List repositories visible to the authenticated GitHub user."""
    return await _client().list_repositories(
        visibility=visibility,
        affiliation=affiliation,
        sort=sort,
        direction=direction,
        per_page=per_page,
        page=page,
    )


@mcp.tool(name="get_repository")
async def get_repository(owner: str, repo: str) -> dict[str, Any]:
    """Return metadata for a specific GitHub repository."""
    return await _client().get_repository(owner=owner, repo=repo)


@mcp.tool(name="list_issues")
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    labels: str | None = None,
    since: str | None = None,
    per_page: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """List issues for a repository."""
    return await _client().list_issues(
        owner=owner,
        repo=repo,
        state=state,
        labels=labels,
        since=since,
        per_page=per_page,
        page=page,
    )


@mcp.tool(name="get_issue")
async def get_issue(owner: str, repo: str, issue_number: int) -> dict[str, Any]:
    """Return a single issue by number."""
    return await _client().get_issue(owner=owner, repo=repo, issue_number=issue_number)


@mcp.tool(name="list_pull_requests")
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    head: str | None = None,
    base: str | None = None,
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """List pull requests for a repository."""
    return await _client().list_pull_requests(
        owner=owner,
        repo=repo,
        state=state,
        head=head,
        base=base,
        sort=sort,
        direction=direction,
        per_page=per_page,
        page=page,
    )


@mcp.tool(name="get_pull_request")
async def get_pull_request(owner: str, repo: str, pull_number: int) -> dict[str, Any]:
    """Return a single pull request by number."""
    return await _client().get_pull_request(owner=owner, repo=repo, pull_number=pull_number)


def main() -> None:
    try:
        mcp.run()
    finally:
        try:
            if _github_client is not None:
                asyncio.run(_github_client.close())
        except Exception:
            pass


if __name__ == "__main__":
    main()
