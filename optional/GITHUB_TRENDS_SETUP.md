# Optional GitHub Trends module

GitHub Trends calculates contribution-oriented language and repository charts from commits.
Its service requires an account registration/authorization step.

## Enable

1. Visit:

```text
https://api.githubtrends.io/auth/signup/public
```

2. Authorize the public account data needed by the service.
3. Confirm that these two URLs render valid SVG cards:

```text
https://api.githubtrends.io/user/svg/ahmadabdullayew/langs?time_range=one_year&include_private=False&loc_metric=changed

https://api.githubtrends.io/user/svg/ahmadabdullayew/repos?time_range=one_year&include_private=False&group=public&loc_metric=changed
```

4. Open `README.md`.
5. Find `OPTIONAL GITHUB TRENDS MODULE`.
6. Move the provided `<p>...</p>` block outside the HTML comment.
7. Commit the change.

## Interpretation

Treat changed lines as activity telemetry, not as a quality or productivity score.
Generated code, repository structure, commit style, refactors, and language verbosity can
all affect line-based measurements.
