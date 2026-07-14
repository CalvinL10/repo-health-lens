from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .models import RepositorySnapshot


class GitHubError(RuntimeError):
    """A readable error returned by the GitHub client."""


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "repo-health-lens/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            f"https://api.github.com{path}", headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                message = json.loads(detail).get("message", detail)
            except json.JSONDecodeError:
                message = detail
            raise GitHubError(f"GitHub returned {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc.reason}") from exc

    def snapshot(self, owner: str, repo: str) -> RepositorySnapshot:
        metadata = self._get(f"/repos/{owner}/{repo}")
        contents = self._get(f"/repos/{owner}/{repo}/contents")
        files = frozenset(
            str(item.get("name", "")).lower()
            for item in contents
            if isinstance(item, dict)
        )
        license_data = metadata.get("license") or {}
        return RepositorySnapshot(
            full_name=metadata["full_name"],
            description=metadata.get("description"),
            default_branch=metadata.get("default_branch", "main"),
            archived=bool(metadata.get("archived")),
            fork=bool(metadata.get("fork")),
            stars=int(metadata.get("stargazers_count", 0)),
            forks=int(metadata.get("forks_count", 0)),
            open_issues=int(metadata.get("open_issues_count", 0)),
            pushed_at=metadata.get("pushed_at"),
            created_at=metadata.get("created_at"),
            license_name=license_data.get("spdx_id"),
            topics=tuple(metadata.get("topics") or ()),
            has_wiki=bool(metadata.get("has_wiki")),
            files=files,
        )

