from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import AnalysisReport, CheckResult, CheckTrend, ScoreTrend


class SnapshotError(ValueError):
    """A snapshot history file is invalid or cannot be written."""


@dataclass(frozen=True)
class SnapshotRecord:
    captured_at: str
    report: AnalysisReport


def _report_to_dict(report: AnalysisReport) -> dict[str, Any]:
    return {
        "repository": report.repository,
        "score": report.score,
        "grade": report.grade,
        "checks": [
            {
                "key": check.key,
                "label": check.label,
                "score": check.score,
                "max_score": check.max_score,
                "evidence": check.evidence,
                "recommendation": check.recommendation,
            }
            for check in report.checks
        ],
    }


def _report_from_dict(payload: Any) -> AnalysisReport:
    if not isinstance(payload, dict):
        raise SnapshotError("Each snapshot report must be an object.")
    try:
        checks = tuple(
            CheckResult(
                key=str(check["key"]),
                label=str(check["label"]),
                score=int(check["score"]),
                max_score=int(check["max_score"]),
                evidence=str(check["evidence"]),
                recommendation=check.get("recommendation"),
            )
            for check in payload["checks"]
        )
        return AnalysisReport(
            repository=str(payload["repository"]),
            score=int(payload["score"]),
            grade=str(payload["grade"]),
            checks=checks,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SnapshotError("Snapshot report has invalid fields.") from exc


def load_history(path: Path) -> tuple[SnapshotRecord, ...]:
    if not path.exists():
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("version") != 1 or not isinstance(payload.get("snapshots"), list):
            raise SnapshotError("Snapshot history must use version 1.")
        return tuple(
            SnapshotRecord(
                captured_at=str(record["captured_at"]),
                report=_report_from_dict(record["report"]),
            )
            for record in payload["snapshots"]
        )
    except SnapshotError:
        raise
    except (OSError, json.JSONDecodeError, AttributeError, KeyError, TypeError) as exc:
        raise SnapshotError(f"Could not read snapshot history: {exc}") from exc


def _trend(previous: SnapshotRecord, current: AnalysisReport) -> ScoreTrend:
    previous_checks = {check.key: check for check in previous.report.checks}
    check_trends = tuple(
        CheckTrend(
            key=check.key,
            label=check.label,
            previous_score=previous_checks[check.key].score,
            current_score=check.score,
            delta=check.score - previous_checks[check.key].score,
        )
        for check in current.checks
        if check.key in previous_checks
    )
    return ScoreTrend(
        previous_captured_at=previous.captured_at,
        previous_score=previous.report.score,
        current_score=current.score,
        delta=current.score - previous.report.score,
        checks=check_trends,
    )


def append_report(
    path: Path, report: AnalysisReport, captured_at: str
) -> ScoreTrend | None:
    history = load_history(path)
    history_repository = history[0].report.repository if history else None
    if path.exists() and not history:
        try:
            history_repository = json.loads(path.read_text(encoding="utf-8")).get(
                "repository"
            )
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise SnapshotError(f"Could not read snapshot history: {exc}") from exc
    if history_repository and history_repository != report.repository:
        raise SnapshotError(
            f"Snapshot history belongs to {history_repository}, not {report.repository}."
        )
    trend = _trend(history[-1], report) if history else None
    updated = history + (SnapshotRecord(captured_at, report),)
    payload = {
        "version": 1,
        "repository": report.repository,
        "snapshots": [
            {"captured_at": item.captured_at, "report": _report_to_dict(item.report)}
            for item in updated
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary:
            json.dump(payload, temporary, indent=2)
            temporary.write("\n")
            temporary_path = temporary.name
        os.replace(temporary_path, path)
    except OSError as exc:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
        raise SnapshotError(f"Could not write snapshot history: {exc}") from exc
    return trend
