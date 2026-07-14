from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RepositorySnapshot:
    full_name: str
    description: str | None
    default_branch: str
    archived: bool
    fork: bool
    stars: int
    forks: int
    open_issues: int
    pushed_at: str | None
    created_at: str | None
    license_name: str | None
    topics: tuple[str, ...]
    has_wiki: bool
    files: frozenset[str]


@dataclass(frozen=True)
class CheckResult:
    key: str
    label: str
    score: int
    max_score: int
    evidence: str
    recommendation: str | None = None


@dataclass(frozen=True)
class AnalysisReport:
    repository: str
    score: int
    grade: str
    checks: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

