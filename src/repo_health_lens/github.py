from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from .models import IssueSummary, RepositorySnapshot


class GitHubError(RuntimeError):
    """A readable error returned by the GitHub client."""


def _repository_path(owner: str, repo: str) -> str:
    if not owner or not repo:
        raise ValueError("owner and repository must be non-empty")
    return f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout = timeout

    def _get(self, path: str, *, allow_not_found: bool = False) -> Any:
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
        except TimeoutError as exc:
            raise GitHubError(
                f"GitHub request timed out after {self.timeout} seconds"
            ) from exc
        except json.JSONDecodeError as exc:
            raise GitHubError("GitHub returned invalid JSON") from exc
        except urllib.error.HTTPError as exc:
            if allow_not_found and exc.code == 404:
                return None
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                message = json.loads(detail).get("message", detail)
            except json.JSONDecodeError:
                message = detail
            remaining = exc.headers.get("X-RateLimit-Remaining")
            rate_limited = (
                exc.code == 429
                or remaining == "0"
                or "rate limit" in str(message).lower()
            )
            if rate_limited:
                reset = exc.headers.get("X-RateLimit-Reset")
                try:
                    reset_at = datetime.fromtimestamp(
                        int(reset), timezone.utc
                    ).isoformat().replace("+00:00", "Z")
                except (TypeError, ValueError, OSError, OverflowError):
                    reset_at = "unknown"
                message = (
                    "API rate limit exceeded "
                    f"(remaining={remaining or 'unknown'}, resets at {reset_at}). "
                    "Set GITHUB_TOKEN for authenticated quota or retry after reset."
                )
            raise GitHubError(f"GitHub returned {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc.reason}") from exc

    def snapshot(self, owner: str, repo: str) -> RepositorySnapshot:
        repository_path = _repository_path(owner, repo)
        metadata = self._get(repository_path)
        contents = self._get(f"{repository_path}/contents")
        workflow_contents = self._get(
            f"{repository_path}/contents/.github/workflows",
            allow_not_found=True,
        ) or ()
        issue_contents = self._get(
            f"{repository_path}/issues?state=all&per_page=100&sort=updated&direction=desc"
        ) or ()
        files = frozenset(
            str(item.get("name", "")).lower()
            for item in contents
            if isinstance(item, dict)
        )
        workflow_files = tuple(
            sorted(
                str(item.get("name", "")).lower()
                for item in workflow_contents
                if isinstance(item, dict)
                and item.get("type") == "file"
                and str(item.get("name", "")).lower().endswith((".yml", ".yaml"))
            )
        )
        issue_activity = []
        for item in issue_contents:
            if not isinstance(item, dict):
                continue
            try:
                number = int(item["number"])
                comments = int(item.get("comments", 0))
            except (KeyError, TypeError, ValueError):
                continue
            issue_activity.append(
                IssueSummary(
                    number=number,
                    kind="pull_request"
                    if item.get("pull_request") is not None
                    else "issue",
                    state=str(item.get("state", "")).lower(),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    closed_at=item.get("closed_at"),
                    comments=max(0, comments),
                )
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
            workflow_files=workflow_files,
            issue_activity=tuple(issue_activity),
        )

