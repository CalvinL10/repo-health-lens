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

## Quick start

Python 3.10 or newer is required.

```bash
python -m repo_health_lens.cli pallets/flask
python -m repo_health_lens.cli pallets/flask --format json
python -m repo_health_lens.cli pallets/flask --format html > report.html
python -m repo_health_lens.cli pallets/flask --snapshot .repo-health/history.json
```

For local development:

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

Unauthenticated requests work for public repositories but are subject to
GitHub's lower API rate limit. Set `GITHUB_TOKEN` if you need a higher limit.
The token only needs read access to public repositories.

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
repository must expose at least one `.yml` or `.yaml` file directly under
`.github/workflows`; an unrelated `.github` directory is not treated as CI. It
does not inspect source code, judge the quality of a README, or reward stars.
Those limitations are deliberate: popularity is not the same as health.

Pass `--snapshot PATH` to append each report to a versioned JSON history file.
When a previous report for the same repository exists, Markdown and JSON output
include the total score delta and changed check scores. The history file is
written atomically and is intended for scheduled local or CI runs.

Pass `--format html` to generate a standalone report with inline CSS. It can be
saved and opened locally without a server or additional assets.

## GitHub Action

Repo Health Lens is also available as a reusable composite action. It writes a
report to the workspace and exposes `score`, `grade`, and `report-path` outputs.
The action does not require a checkout of the repository containing the action:

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
```

Set `snapshot` to a JSON history path when a workflow should track score trends.
For private repositories, pass a token with read access through the `token`
input and grant the workflow only the permissions it needs.

## Roadmap

The reusable GitHub Action is now available. Future improvements should be
proposed as focused issues with explainable, observable scoring criteria.

## Responsible use

Do not use this score to rank or shame maintainers. Repository context matters,
and archived or quiet software can still be excellent. When studying another
project, respect its license and attribution requirements.

## Contributing

Issues and focused pull requests are welcome. Please include tests for scoring
changes and explain why a new signal is fair, observable, and difficult to game.

## License

MIT

