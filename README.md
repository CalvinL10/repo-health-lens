# Repo Health Lens

Repo Health Lens turns public GitHub metadata into a transparent, actionable
repository health report. It is designed for maintainers, contributors, and
learners who want more than a mysterious single score.

The first release evaluates six signals:

- recent maintenance activity;
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
| Recent activity | 25 |
| Discoverability and docs | 20 |
| Contributor readiness | 15 |
| Engineering signals | 20 |
| License and security | 15 |
| Original project signal | 5 |

This early version only checks repository-level signals. It does not inspect
source code, judge the quality of a README, or reward stars. Those limitations
are deliberate: popularity is not the same as health.

## Roadmap

- inspect workflow files instead of treating `.github` as a CI signal;
- report issue and pull-request responsiveness;
- support saved snapshots and score trends;
- generate a standalone HTML report;
- publish a reusable GitHub Action.

## Responsible use

Do not use this score to rank or shame maintainers. Repository context matters,
and archived or quiet software can still be excellent. When studying another
project, respect its license and attribution requirements.

## Contributing

Issues and focused pull requests are welcome. Please include tests for scoring
changes and explain why a new signal is fair, observable, and difficult to game.

## License

MIT

