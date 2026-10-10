# Contribution generation — operator notes

This file covers only Phase 5 contribution generation; the authoritative profile policy remains `profile-spec.json`.

## Run

The workflow at `.github/workflows/update-contributions.yml` schedules the generator daily.
The same script can be invoked locally from **any current working directory**:

```bash
PROFILE_USERNAME=ahmadabdullayew GITHUB_TOKEN=<token> python3 scripts/generate_contributions.py
```

Do not commit a token. The workflow uses the ephemeral GitHub Actions token.
The script writes to the repository derived from its own file path.

## Outputs and freshness

The five owned outputs under `profile/` are four desktop/mobile, light/dark static SVGs and one accessible Markdown table. They must be published as one coherent set. The reporting dates and total are data returned by GitHub. The **retrieval timestamp** is the UTC time captured after the successful API response and explicitly does not turn the archived Phase 4 snapshot into a fresh result. The archived timestamp is unknown.

## Failures and recovery

Schema failures, GraphQL errors, insufficient or malformed data, inconsistent counts/dates, invalid SVG/XML, and unbounded output are rejected. HTTP retries are limited to three calls with bounded waits; 401 and other permanent HTTP failures are not retried. Generation should exit nonzero before publishing when input is invalid.

Publication creates temporary `.profile-candidate-*` staging and `.profile-previous-*` backup directories under the repository root. On a normal failure it restores the old `profile/`. If an abrupt termination occurs during the short rename window, inspect the root for a `.profile-previous-*` directory. If `profile/` is absent and the previous directory is intact, restore it manually from the backup **only after confirming no other generator is running**. Never delete backup files until verified.

The workflow validates the static visuals, the README contract, and all regression tests before a single Git commit stages the owned files. Its successful schedule does not by itself guarantee the public GitHub profile is fresh; check the summary's UTC retrieval timestamp and GitHub Actions run status.

## Local checks

```bash
python3 -m pip install -r requirements-validation.txt -r requirements-visual.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_profile.py
python3 scripts/check_visuals.py
```

No network access is required for the maintained tests. Do not run a live generator from a CI fixture with an arbitrary token; the tests inject deterministic fake responses.

## Phase 6 — split job publication (supersedes the older single-job push procedure)

The **generate** job has `contents: read`, checks out without cached write credentials, fetches the live GraphQL calendar, and runs all local quality checks. It creates a short-lived ZIP candidate with the exact five allowlisted assets, SHA-256 digests, the source commit SHA, the daily/period count, and a UTC capture timestamp. `actions/upload-artifact` transfers this immutable candidate to the next job; it never carries a repository token or executable instruction.

The **publish** job is the only workflow job that holds write privileges (`contents: write` and `pull-requests: write`). It inspects every candidate byte, enforces a **six-hour maximum age**, fetches the current `main` tip, and refuses to publish if README/spec/generator/workflow/owned assets changed since the generator's source commit. It validates all five assets and reruns the complete suite **after** applying them to the newest base, before staging only the allowlisted five paths. It attempts a fast-forward-only push with at most three retries for genuine concurrent changes. It NEVER force-pushes `main` or bypasses rulesets.

If direct push is rejected by branch protection, the publisher creates a unique automation branch and asks GitHub CLI to open a pull request. That status is **pending manual merge**, not a completed publication. If the repository disallows Actions-created pull requests, the workflow fails and logs the pushed branch name so the maintainer can open a PR manually. `GITHUB_TOKEN`-authored PRs may not trigger ordinary `pull_request` checks; explicitly run **Profile quality** via `workflow_dispatch` on the PR branch before merging. If required checks or approvals are configured, merging must follow those policies. No bypass credential is stored.

On a successful direct main push, the publishing job checks the immutable raw files for the committed SHA and checks that the public profile HTML includes expected project headings. On a human-merged PR or manual push, the quality workflow repeats this verification against that commit. These checks **do not prove visual rendering or assistive-technology accessibility**; the manual checklist in `PUBLICATION_RUNBOOK.md` remains mandatory.

The initial archived snapshot still has **unknown retrieval time** and must not be repackaged as fresh. Generate a new authenticated snapshot before invoking the bundle or publishing commands. The live GitHub workflow has not been run from this local artifact; initial workflow permission settings and protected-branch behavior must be checked in GitHub UI.

