from __future__ import annotations

import httpx

from octopal.mcp_servers.github import (
    _normalize_issue,
    _normalize_pull_request,
    _normalize_repo,
    _parse_github_api_error,
)


def test_normalize_repo_keeps_expected_fields() -> None:
    normalized = _normalize_repo(
        {
            "id": 1,
            "name": "demo",
            "full_name": "octo/demo",
            "private": False,
            "default_branch": "main",
            "html_url": "https://github.com/octo/demo",
            "owner": {
                "login": "octo",
                "id": 9,
                "type": "User",
                "site_admin": False,
                "html_url": "https://github.com/octo",
            },
        }
    )

    assert normalized["full_name"] == "octo/demo"
    assert normalized["owner"]["login"] == "octo"


def test_normalize_issue_keeps_labels_and_user() -> None:
    normalized = _normalize_issue(
        {
            "id": 2,
            "number": 17,
            "title": "Fix connector",
            "state": "open",
            "user": {"login": "alice", "id": 10, "type": "User", "site_admin": False},
            "labels": [{"name": "bug", "color": "d73a4a", "description": "Something is broken"}],
        }
    )

    assert normalized["number"] == 17
    assert normalized["user"]["login"] == "alice"
    assert normalized["labels"][0]["name"] == "bug"


def test_normalize_pull_request_keeps_base_and_head_refs() -> None:
    normalized = _normalize_pull_request(
        {
            "id": 3,
            "number": 8,
            "title": "Add connector",
            "state": "open",
            "head": {"label": "octo:feature", "ref": "feature", "sha": "abc123"},
            "base": {"label": "octo:main", "ref": "main", "sha": "def456"},
            "user": {"login": "bob", "id": 11, "type": "User", "site_admin": False},
        }
    )

    assert normalized["number"] == 8
    assert normalized["head"]["ref"] == "feature"
    assert normalized["base"]["ref"] == "main"


def test_parse_github_api_error_prefers_message_from_json_payload() -> None:
    response = httpx.Response(
        403,
        json={"message": "Resource not accessible by personal access token", "documentation_url": "https://docs.github.com"},
    )

    error = _parse_github_api_error(response)

    assert error.status_code == 403
    assert str(error) == "GitHub API 403: Resource not accessible by personal access token"
