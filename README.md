# Repo Health Lens

Repo Health Lens turns public GitHub metadata into a transparent, actionable
repository health report. It is designed for maintainers, contributors, and
learners who want more than a mysterious single score.

The first release evaluates seven signals:

- recent maintenance activity;
- issue and pull-request responsiveness;
- discoverability and documentation;
- contributor readiness;
- tests and automation;
- licensing and security guidance;
- whether the repository is an original project or a fork.

Every point is backed by visible evidence, and every weak area produces a
specific next step. The score is a conversation starter, not a claim about code
quality or maintainer competence.

## Who it is for

Repo Health Lens is for:

- maintainers doing a lightweight weekly review of a public repository;
- contributors who want evidence before suggesting documentation, testing, or
  community-process improvements;
- teams that want a readable report artifact from GitHub Actions without
  turning the score into a merge gate.

It answers one narrow question: **which observable repository-level signals are
healthy, which need attention, and what is the next practical action?** It does
not review source-code quality, maintainer competence, or project popularity.

## Quick start

Python 3.10 or newer is required.

Install from a local checkout:

```bash
python -m pip install -e .
```

Or install the current packaged code directly from GitHub:

```bash
python -m pip install "repo-health-lens @ git+https://github.com/CalvinL10/repo-health-lens.git@main"
```

The `main` ref is used here because the v0.1.0 tag has not been published
yet. Once that release is tagged, pin the command to `@v0.1.0` when you need a
fixed release rather than the latest packaging changes.

Run a report by replacing `OWNER/REPOSITORY` with the public GitHub repository
you want to inspect:

```bash
repo-health-lens pallets/flask
repo-health-lens pallets/flask --format json
repo-health-lens pallets/flask --format html > report.html
repo-health-lens pallets/flask --snapshot .repo-health/history.json
```

The same commands work with `python -m repo_health_lens.cli` when running from
an installed checkout. The Markdown report gives you the complete path:
`OWNER/REPOSITORY` → public GitHub evidence → per-check scores → total grade →
recommended next steps. JSON is for automation, while HTML is a standalone
file you can open or attach to an issue. Snapshot history adds the score delta
and changed checks on later runs.

For local development, the editable install above is enough; the test suite
can be run with:

```bash
python -m unittest discover -s tests
```

Unauthenticated requests work for public repositories but are subject to
GitHub's lower API rate limit. Set `GITHUB_TOKEN` if you need a higher limit.
The token only needs read access to public repositories.

On PowerShell, set the token for the current terminal session without putting
it in the repository:

```powershell
$env:GITHUB_TOKEN = "github_pat_your_token"
python -m repo_health_lens.cli pallets/flask
```

If the API limit is exhausted, Repo Health Lens reports the remaining quota and
the UTC reset time. Never commit the token or print it in logs.

## How scoring works

The 100 available points are intentionally easy to audit:

| Area | Points |
|---|---:|
| Recent activity | 15 |
| Issue and pull-request responsiveness | 10 |
| Discoverability and docs | 20 |
| Contributor readiness | 15 |
| Engineering signals | 20 |
| License and security | 15 |
| Original project signal | 5 |

This early version only checks repository-level signals. For responsiveness, it
samples up to 100 of the most recently updated issues and pull requests. The
report uses public comment counts, update age, and stale open work as
observable activity proxies; it cannot identify whether a comment came from a
maintainer or measure the quality of a response. For engineering signals, a
repository must expose a conventional test directory (`test`, `tests`, `spec`,
or `specs`) or a recognizable root-level Python, Go, Rust, JavaScript, or
TypeScript test file name (`test_*`, `*_test.*`, `*.test.*`, or `*.spec.*`),
plus at least one `.yml` or `.yaml` file directly under `.github/workflows`; an
unrelated `.github` directory is not treated as CI. The
root, `.github`, `docs`, and workflow directory checks read entries across
100-entry pages, subject to GitHub's Contents API limits, but they do not
recursively inspect source code or directories. Standard README, contributing,
code-of-conduct, and security files found directly in `.github` or `docs` count
the same as root files; regular files and symlinks count, while Git submodules
do not. The report also does not judge the quality
of a README or reward stars. Those limitations are deliberate: popularity is
not the same as health.
License points require GitHub to report a recognized SPDX license; an
`NOASSERTION` response is treated as an unknown license.

Pass `--snapshot PATH` to append each report to a versioned JSON history file.
When a previous report for the same repository exists, Markdown and JSON output
include the total score delta and changed check scores. The history file is
written atomically and is intended for scheduled local or CI runs.

Pass `--format html` to generate a standalone report with inline CSS. It can be
saved and opened locally without a server or additional assets.

## Demo

Open the [sample HTML report for pallets/flask](docs/demo/flask-health.html)
to see the standalone output. It is generated from public GitHub metadata and
can be reproduced with:

```bash
python -m repo_health_lens.cli pallets/flask --format html > flask-health.html
```

## Three practical workflows

### Weekly maintainer review

Run the Markdown report with `--snapshot` for the repository you maintain.
Review the evidence behind each check, then use the recommended next steps to
choose one small follow-up rather than treating the total as a verdict.

### Contributor or project triage

Generate the HTML report for a project you are considering contributing to.
Use the evidence to distinguish missing contributor guidance, tests, or CI from
signals that are simply not observable through the public GitHub API.

### Scheduled team report

Use the GitHub Action to publish a Markdown or HTML artifact on a schedule.
Read `score`, `grade`, and `report-path` as workflow outputs, but keep the
Action informational: this v0.1 score is not a quality gate and should not
block merges by itself.

## GitHub Action

Repo Health Lens is also available as a reusable composite action. It writes a
report to the workspace and exposes `score`, `grade`, and `report-path` outputs.
The action does not require a checkout of the repository containing the action:
The example uses `@main` because the v0.1.0 tag has not been published yet;
replace it with `@v0.1.0` once that release is tagged when you need a fixed
action version.

```yaml
permissions:
  contents: read

steps:
  - uses: CalvinL10/repo-health-lens@main
    id: health
    with:
      repository: pallets/flask
      format: html
      output: artifacts/flask-health.html
  - run: echo "Health score: ${{ steps.health.outputs.score }} (${{ steps.health.outputs.grade }})"
  - name: Upload the report
    uses: actions/upload-artifact@v4
    with:
      name: repo-health-lens-report
      path: artifacts/flask-health.html
```

Set `snapshot` to a JSON history path when a workflow should track score trends.
For private repositories, pass a token with read access through the `token`
input and grant the workflow only the permissions it needs.
The `output` and `snapshot` paths are resolved relative to `GITHUB_WORKSPACE`
and are rejected if they escape the workspace.
The health action writes the report into the workflow workspace; the upload
step above keeps it available as a downloadable workflow artifact after the
job finishes.

## Roadmap

### v0.1.0

- [x] Explainable repository-level scoring
- [x] Markdown, JSON, and standalone HTML reports
- [x] Snapshot history and score trends
- [x] Reusable GitHub Action with outputs

### Next

Propose focused issues for scoring improvements, release hardening, or new
observable signals. Each change should define a fair criterion and a testable
user outcome before implementation.

## Responsible use

Do not use this score to rank or shame maintainers. Repository context matters,
and archived or quiet software can still be excellent. When studying another
project, respect its license and attribution requirements.

## Contributing

Issues and focused pull requests are welcome. Please include tests for scoring
changes and explain why a new signal is fair, observable, and difficult to game.

## License

MIT

