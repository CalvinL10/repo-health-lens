from __future__ import annotations

from datetime import datetime, timezone

from .models import AnalysisReport, CheckResult, RepositorySnapshot


def _days_since(value: str | None, now: datetime) -> int | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return max(0, (now - parsed).days)


def _file_present(files: frozenset[str], names: tuple[str, ...]) -> bool:
    return any(name in files for name in names)


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _responsiveness(snapshot: RepositorySnapshot, now: datetime) -> tuple[int, str, str | None]:
    items = snapshot.issue_activity
    if not items:
        return (
            0,
            "No issue or pull-request activity was returned by GitHub.",
            "Review issue and pull-request activity when public activity is available.",
        )

    ages = [
        _days_since(item.updated_at or item.created_at, now)
        for item in items
    ]
    known_ages = [age for age in ages if age is not None]
    commented = sum(item.comments > 0 for item in items)
    recent = sum(age is not None and age <= 30 for age in ages)
    open_items = [item for item in items if item.state == "open"]
    open_ages = [
        _days_since(item.updated_at or item.created_at, now)
        for item in open_items
    ]
    stale_open = sum(age is not None and age > 90 for age in open_ages)

    comment_points = (commented * 4) // len(items)
    if any(age <= 30 for age in known_ages):
        freshness_points = 3
    elif any(age <= 90 for age in known_ages):
        freshness_points = 2
    elif any(age <= 365 for age in known_ages):
        freshness_points = 1
    else:
        freshness_points = 0

    if not open_items or stale_open == 0:
        queue_points = 3
    else:
        stale_ratio = stale_open / len(open_items)
        queue_points = 2 if stale_ratio <= 0.25 else 1 if stale_ratio <= 0.5 else 0

    score = comment_points + freshness_points + queue_points
    issue_count = sum(item.kind == "issue" for item in items)
    pull_request_count = sum(item.kind == "pull_request" for item in items)
    evidence = (
        f"Sampled items={len(items)}, issues={issue_count}, "
        f"pull requests={pull_request_count}, comments={commented}/{len(items)}, "
        f"recently updated <=30d={recent}, stale open={stale_open}."
    )
    recommendation = (
        None
        if score == 10
        else "Respond to open issues and pull requests, especially stale items."
    )
    return score, evidence, recommendation


def analyze_repository(
    snapshot: RepositorySnapshot, now: datetime | None = None
) -> AnalysisReport:
    now = now or datetime.now(timezone.utc)
    age = _days_since(snapshot.pushed_at, now)
    if snapshot.archived:
        activity_score, activity_evidence = 0, "Repository is archived."
    elif age is None:
        activity_score, activity_evidence = 0, "No push date is available."
    elif age <= 30:
        activity_score, activity_evidence = 15, f"Last push was {age} days ago."
    elif age <= 90:
        activity_score, activity_evidence = 11, f"Last push was {age} days ago."
    elif age <= 365:
        activity_score, activity_evidence = 6, f"Last push was {age} days ago."
    else:
        activity_score, activity_evidence = 1, f"Last push was {age} days ago."

    has_readme = _file_present(
        snapshot.files, ("readme.md", "readme.rst", "readme.txt", "readme")
    )
    has_contributing = _file_present(
        snapshot.files, ("contributing.md", "contributing.rst")
    )
    has_code_of_conduct = _file_present(
        snapshot.files, ("code_of_conduct.md", "code-of-conduct.md")
    )
    has_tests = "tests" in snapshot.files or "test" in snapshot.files
    has_workflows = bool(snapshot.workflow_files)
    has_security = "security.md" in snapshot.files

    docs_score = (
        (12 if has_readme else 0)
        + (5 if snapshot.description else 0)
        + (3 if snapshot.topics else 0)
    )
    community_score = (
        (7 if has_contributing else 0)
        + (5 if has_code_of_conduct else 0)
        + (3 if snapshot.has_wiki else 0)
    )
    engineering_score = (10 if has_tests else 0) + (10 if has_workflows else 0)
    governance_score = (10 if snapshot.license_name else 0) + (
        5 if has_security else 0
    )
    responsiveness_score, responsiveness_evidence, responsiveness_recommendation = (
        _responsiveness(snapshot, now)
    )

    checks = (
        CheckResult(
            "activity",
            "Recent activity",
            activity_score,
            15,
            activity_evidence,
            None if activity_score >= 11 else "Publish a scoped maintenance update.",
        ),
        CheckResult(
            "responsiveness",
            "Issue and pull-request responsiveness",
            responsiveness_score,
            10,
            responsiveness_evidence,
            responsiveness_recommendation,
        ),
        CheckResult(
            "documentation",
            "Discoverability and docs",
            docs_score,
            20,
            f"README={has_readme}, description={bool(snapshot.description)}, topics={bool(snapshot.topics)}.",
            None if docs_score == 20 else "Add a focused README, description, and topics.",
        ),
        CheckResult(
            "community",
            "Contributor readiness",
            community_score,
            15,
            f"Contributing={has_contributing}, conduct={has_code_of_conduct}, wiki={snapshot.has_wiki}.",
            None if community_score >= 12 else "Document how contributors can participate.",
        ),
        CheckResult(
            "engineering",
            "Engineering signals",
            engineering_score,
            20,
            f"Tests={has_tests}, workflow files={len(snapshot.workflow_files)}.",
            None
            if engineering_score == 20
            else "Add automated tests and a GitHub Actions workflow.",
        ),
        CheckResult(
            "governance",
            "License and security",
            governance_score,
            15,
            f"License={snapshot.license_name or 'missing'}, security policy={has_security}.",
            None if governance_score == 15 else "Add a license and security policy.",
        ),
        CheckResult(
            "originality",
            "Original project signal",
            5 if not snapshot.fork else 0,
            5,
            "Repository is original." if not snapshot.fork else "Repository is a fork.",
            None if not snapshot.fork else "Explain the project's distinct value clearly.",
        ),
    )
    score = sum(check.score for check in checks)
    return AnalysisReport(snapshot.full_name, score, _grade(score), checks)

