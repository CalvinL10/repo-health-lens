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
        activity_score, activity_evidence = 25, f"Last push was {age} days ago."
    elif age <= 90:
        activity_score, activity_evidence = 18, f"Last push was {age} days ago."
    elif age <= 365:
        activity_score, activity_evidence = 10, f"Last push was {age} days ago."
    else:
        activity_score, activity_evidence = 2, f"Last push was {age} days ago."

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
    has_ci = ".github" in snapshot.files
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
    engineering_score = (10 if has_tests else 0) + (10 if has_ci else 0)
    governance_score = (10 if snapshot.license_name else 0) + (
        5 if has_security else 0
    )

    checks = (
        CheckResult(
            "activity",
            "Recent activity",
            activity_score,
            25,
            activity_evidence,
            None if activity_score >= 18 else "Publish a scoped maintenance update.",
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
            f"Tests={has_tests}, GitHub configuration={has_ci}.",
            None if engineering_score == 20 else "Add automated tests and CI.",
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

