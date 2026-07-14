# Security policy

Please report suspected vulnerabilities privately through GitHub's security
advisory feature. Do not include access tokens or private repository data in a
public issue.

Repo Health Lens sends requests only to the GitHub API. Tokens are read from the
`GITHUB_TOKEN` environment variable and must never be logged or committed.

