# GitHub profile publication and recovery runbook

**Last local review:** 2026-10-10. **Deployment state:** offline/local checks completed only; this ZIP does not represent a live push or verified live rendering.

## Ownership, privilege boundary, and freshness

- Only `.github/workflows/update-contributions.yml` updates the five paths under `profile/`: `contributions-dark.svg`, `contributions-light.svg`, `contributions-mobile-dark.svg`, `contributions-mobile-light.svg`, `contributions-summary.md`.
- `generate` uses a read-only `GITHUB_TOKEN`, no persisted checkout credentials, immutable pinned GitHub Actions, and ephemeral upload of a verified, allowlisted candidate. `publish` uses separate job-scoped write permission, downloads the immutable artifact, verifies a manifest and bytes, fetches latest `main`, reruns tests, then pushes only the five paths.
- A candidate is **fresh** only when the UTC retrieval timestamp from a successfully validated GraphQL response is within six hours of publication. A scheduled event or green workflow by itself is **not** evidence of a successful public update. The archive's historical `unknown` timestamp is never upgraded by assertion.
- A successful **direct-main** status means Git accepted the candidate commit. A **pull-request** status means the candidate is **not live on main**. **unchanged** means publication required no content change. **failed** means no successful publication has been established. A public HTTPS check and manual GitHub UI review remain separate.
- There is exactly one generating/publishing workflow and one shared concurrency group. `cancel-in-progress: false` prevents scheduled/manual runs from terminating an active publication.

## Installation and initial checks

1. Review this ZIP and push source changes to the profile repository via the normal, reviewed Git process. This artifact does **not** push itself.
2. Confirm the GitHub repository is `ahmadabdullayew/ahmadabdullayew`, the default branch is `main`, and the workflow is enabled. Confirm branch protection/ruleset state in **Settings → Rules → Rulesets** and **Settings → Branches**, using an account with sufficient permissions. API inspection of branch protection returned **403 Resource not accessible by integration** during the local review; **no permission to push main has been inferred**. The public rulesets listing returned `[]` at that time, which is not proof that all protection mechanisms are absent.
3. In **Settings → Actions → General**, confirm workflow permissions support `contents: write`, and (for fallback) **Allow GitHub Actions to create and approve pull requests** is enabled if organizational policy permits. If not, expect a blocked automated PR and follow the manual branch recovery below. Do not weaken branch protections simply to enable this workflow.
4. Ensure the pinned actions remain reviewed and permitted by organization/repository action policy. They are referenced by their exact 40-hex SHAs.
5. Run: `python3 -m pip install -r requirements-validation.txt -r requirements-visual.txt`, `python3 -m unittest discover -s tests -v`, `python3 scripts/validate_profile.py`, `python3 scripts/check_visuals.py`.
6. Manually run **Update contribution calendar** on `main` in GitHub Actions. Review both jobs and the job summary. Check the freshness timestamp in `profile/contributions-summary.md` **on the main branch** after publication or PR merge.

## Branch protection and push conflicts

- The publisher only uses a **fast-forward** main push. A race causes a bounded refresh/revalidate/retry. If the README, generator, workflow, policy, or owned assets changed after the candidate's source commit, publishing **stops** and demands a fresh generation; it does not overwrite new changes.
- If the direct main push is denied, the workflow attempts to create `automation/profile-activity-<run-id>-<attempt>` and opens a PR. It never uses `--force` on main, impersonates an administrator, or disables required checks. PRs created using the default GitHub token may need a manual `workflow_dispatch` of **Profile quality** on that branch to satisfy checks.
- If PR creation fails, find the pushed automation branch in the job logs, open a PR yourself, run required CI, and merge only after review. If the branch itself was rejected, no remote publication occurred; correct permissions and rerun generation.

## Local candidate diagnostics

```bash
# The archived files have no trusted retrieval timestamp; do NOT bundle them directly.
PROFILE_USERNAME=ahmadabdullayew GITHUB_TOKEN='<redacted>' python3 scripts/generate_contributions.py
python3 -m unittest discover -s tests -v
python3 scripts/check_visuals.py
python3 scripts/validate_profile.py
python3 scripts/profile_release.py bundle --source-sha "$(git rev-parse HEAD)" --output /tmp/profile-assets.zip
python3 scripts/profile_release.py inspect --bundle /tmp/profile-assets.zip
```

- Do not print or commit access tokens. Candidate files and all other generated outputs must be inspected before they are merged or published.
- `PROFILE_RELEASE_ERROR` identifies a failed local consistency check. If a git push is rejected, the logs distinguish a race retry from PR fallback. A green **generate** job alone does not mean the profile was published.
- A failed **public verification** after a successful Git push is an *unverified publication*, not proof that a rollback happened. Inspect the actual commit and profile promptly.

## Emergency recovery and rollback

1. Inspect the last known-good main commit (`git log --oneline -- profile/`) and the failed run's summary; stop further manual triggers while diagnosing.
2. If a generated commit was published with incorrect assets, **revert that commit through a reviewed PR** (`git revert <bad-commit>` on a recovery branch, then merge according to branch policy), rather than force-pushing `main`.
3. If no remote publication occurred, leave main untouched and fix the underlying API/validation/workflow problem before a new run.
4. If a local generator aborted during its directory replacement, inspect `.profile-previous-*` and `.profile-candidate-*` under the repository root; restore the last intact backup only when no other generator is running. See `CONTRIBUTION_GENERATION.md`.
5. Re-run local checks, trigger the publishing workflow, confirm the job summary, and inspect the public profile and numerical snapshot. Record the incident and recovery action in repository history.

## End-to-end acceptance (after real publishing)

- [ ] **GitHub Actions**: source-quality checks, generator, staged candidate, publisher and public verification all green (or reviewed PR merged and then public checks green).
- [ ] **Ownership/permissions**: output diff contains exactly the registered paths and no extra files; branch protection has not been bypassed.
- [ ] **Freshness**: public `profile/contributions-summary.md` has real UTC retrieval time (within policy) and matching date/count data.
- [ ] **Desktop**: inspect the actual GitHub profile in light/dark themes at 768, 1024 and 1440 CSS px; headings and linked illustrations display correctly.
- [ ] **Mobile**: inspect at 320 and 390 CSS px, light/dark; mobile summary is legible, no clipped labels, and the numeric table is reachable.
- [ ] **Keyboard / assistive tech**: validate focus order, accessible link labels, SVG alternatives and usable text-equivalent contribution data with an actual browser and screen reader. Automated raster/HTML checks cannot certify this.
- [ ] **Navigation**: verify featured GitHub project links, CV, evidence index, contact link, and the numeric daily/monthly table. LinkedIn and any external destination require independent review if not accessible in this environment.
- [ ] **Incident trace**: record workflow run URL, published commit SHA, verification date, and any deviations in the release/PR notes.

