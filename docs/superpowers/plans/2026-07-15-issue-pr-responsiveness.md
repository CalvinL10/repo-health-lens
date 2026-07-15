# Issue and Pull-Request Responsiveness Implementation Plan

> For agentic workers: Execute this plan inline with test-first checkpoints.

**Goal:** Add an explainable responsiveness signal backed by recent GitHub issue and pull-request metadata.

**Architecture:** Extend RepositorySnapshot with compact IssueSummary records. GitHubClient.snapshot() reads the repository issues endpoint, which includes pull requests, and records only stable public fields. analyze_repository() adds a 10-point responsiveness check using comment coverage, recent updates, and stale open work; existing checks are rebalanced so the report remains out of 100. The report and README explain the sampled, observable proxy.

**Tech Stack:** Python 3.10+, stdlib dataclasses, urllib, and unittest.

---

### Task 1: Define activity data and scoring behavior

**Files:**
- Modify: src/repo_health_lens/models.py
- Modify: src/repo_health_lens/analysis.py
- Test: tests/test_analysis.py

- [x] Add tests for a fully responsive issue/PR sample scoring 10/10, a stale unanswered sample receiving a lower score and recommendation, and empty activity receiving an explicit "not enough activity" recommendation.
- [x] Run python -m unittest tests.test_analysis; confirm the new tests fail because IssueSummary and responsiveness scoring do not exist.
- [x] Add IssueSummary and issue_activity to the snapshot model, add a 10-point responsiveness check, reduce recent activity to 15 points, and keep all report totals at 100.
- [x] Run the analysis tests and the full suite; confirm all pass.

### Task 2: Read issue and pull-request metadata from GitHub

**Files:**
- Modify: src/repo_health_lens/github.py
- Test: tests/test_github.py

- [x] Add a client test proving issue records and pull requests from the /issues endpoint become typed summaries while malformed entries are ignored.
- [x] Run the focused client test; confirm it fails before the endpoint and mapping exist.
- [x] Fetch /repos/{owner}/{repo}/issues?state=all&per_page=100&sort=updated&direction=desc, map issue/PR kind, state, timestamps, and comment counts, and preserve GitHub error handling.
- [x] Run the focused client tests and the full suite.

### Task 3: Document the observable signal

**Files:**
- Modify: README.md
- Modify: tests/test_render.py

- [x] Assert rendered reports expose the responsiveness check and its recommendation when activity data is unavailable.
- [x] Update the scoring table, signal limitations, and roadmap entry to describe the 100-item issue/PR sample and proxy metrics.
- [x] Run the complete test suite.

### Task 4: Verify and deliver

**Files:**
- No additional source files.

- [x] Run python -m unittest discover -s tests.
- [x] Review the diff and ensure no user changes were overwritten.
- [ ] Commit the substantive implementation with feat: report issue and pull-request responsiveness.
- [ ] Push main to origin and record the resulting commit and remote/CI status.
