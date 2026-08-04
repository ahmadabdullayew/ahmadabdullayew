# Widget setup

The default profile is intentionally usable before any workflow runs. Placeholder SVGs are
committed under `profile/` and are replaced by generated cards.

## 1. Profile cards

The workflow `.github/workflows/profile-cards.yml` creates:

- `profile/stats.svg`
- `profile/top-langs.svg`
- `profile/streak.svg`

It uses the maintained action recommended by the former GitHub Readme Stats project and the
static-generation mode of GitHub Readme Streak Stats.

After pushing the repository:

1. Open the repository on GitHub.
2. Open **Actions**.
3. Select **Update profile cards**.
4. Choose **Run workflow**.
5. Confirm that the workflow commits the generated SVG files.

No personal access token is required for public data.

## 2. Extended Metrics

`lowlighter/metrics` needs a personal access token because repository-scoped `GITHUB_TOKEN`
cannot read all user-level activity data.

Create a classic personal access token with **no scopes** for public-only metrics:

1. GitHub → Settings → Developer settings.
2. Personal access tokens.
3. Create a token with the least possible privileges.
4. Open `ahmadabdullayew/ahmadabdullayew`.
5. Settings → Secrets and variables → Actions.
6. Add a repository secret named exactly:

```text
METRICS_TOKEN
```

7. Open Actions → **Update extended metrics** → **Run workflow**.

Do not place the token inside a YAML file or README. Add broader scopes only when you
deliberately choose to include private or organization data.

## 3. Typing SVG

The typing line is intentionally limited to two evidence-oriented statements. It is a
non-critical hosted enhancement: the textual positioning below it remains visible if the
service fails.

## 4. Profile views

The counter is placed at the bottom and treated only as lightweight traffic telemetry.
It is not presented as a professional achievement.

## 5. GitHub Trends

See `optional/GITHUB_TRENDS_SETUP.md`. The module is disabled by default because GitHub
Trends requires account authorization before its user SVG endpoints reliably render.
