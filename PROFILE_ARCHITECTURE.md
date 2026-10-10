# Profile architecture and editorial contract

## Scope and authority

**`profile-spec.json` is the authoritative, machine-readable repository contract.**
`README.md` is the rendered public profile; the validation script implements the
contract; this document explains its rationale. If the three disagree, amend the
manifest and implementation in the same change; do not silently add a parallel
set of hard-coded rules. Project claims remain unmodified through Phase 2 and are not represented as
independently audited.

The permitted README structure, in order, is:

1. About
2. Featured Projects
3. ML Experience and Research
4. Technical Foundation
5. GitHub Activity
6. Current Focus
7. Connect

`CV.md` and `PROJECT_EVIDENCE.md` are repository-owned, inspectable
supporting documents linked from the README. Their presence and local links are
part of the public portfolio; they do not replace the README's concise account.

The profile begins with semantic text identity and linked project evidence, plus
explicit contact paths and a link to the official GitHub activity page. The README
may contain Markdown headings, prose, links, tables, lists and fenced code;
restricted semantic HTML is used solely for the responsive contribution picture. The public README may not
embed externally generated images. Local image references must be registered in
`profile-spec.json`. This restriction concerns images, not regular outbound links.

## Publication architecture

**One primary activity representation:** the repository-owned, static light/dark
contribution calendar (`profile/contributions-{dark,light}.svg`) with smaller-screen
monthly-count variants (`profile/contributions-mobile-{dark,light}.svg`) and
a numerical accessible equivalent (`profile/contributions-summary.md`). It comes from
GitHub's contribution GraphQL response; the images in source control constitute
the last successfully published snapshot. The README links to the live GitHub
contribution page rather than pretending that a scheduled job always succeeds.

The previously unused local statistics/top-language generation workflow has been
removed, together with externally hosted statistics, top-language and streak
cards. Those files were absent from the supplied source archive; they are *not*
required outputs under the selected architecture. They should not be reintroduced
without an explicit decision to replace the current activity representation.

This design is intentionally minimal: no second statistics system, no parallel
streak service, and no third-party badges or decorative image API calls. It
remains valid if the calendar becomes unavailable: the accessible numerical report and
live GitHub activity link still exist. The animation was removed in Phase 4. Phase 5 implements validated input,
bounded API retries, snapshot provenance, and staged, recoverable publication.
The five assets are emitted from one validated API response, tested before
publishing, and committed together by the scheduled GitHub workflow.

## Asset registry and ownership

| Asset | Maintainer / generator | Publishing mechanism | Purpose |
| --- | --- | --- | --- |
| `profile/contributions-dark.svg` | `scripts/generate_contributions.py` | `.github/workflows/update-contributions.yml` | Static desktop dark calendar |
| `profile/contributions-light.svg` | Same generator | Same workflow | Static desktop light calendar |
| `profile/contributions-mobile-dark.svg` | Same generator | Same workflow | Static mobile dark monthly counts |
| `profile/contributions-mobile-light.svg` | Same generator | Same workflow | Static mobile light monthly counts |
| `profile/contributions-summary.md` | Same generator | Same workflow | Accessible complete numeric report (not an image asset) |

Phase 1 originally integrated the preexisting `assets/hero.svg` and
`assets/ml-system.svg`. **Phase 4 deliberately retired them**: the banner
repeated the identity and delayed engineering evidence, while the 1200px
methodology illustration became difficult to read on narrow screens. Its
substantive engineering principle remains in plain README text. Both files were
removed from the asset registry and filesystem; the previous Phase 1 integration
record is historical, not an instruction to restore them.

Every embedded image must be registered in `profile-spec.json`. Generator-owned
assets must only be written by their generator. The generated Markdown report
is declared under `publication.accessible_summary`, not in the image registry.

## External image policy

- **Embedded remote image URLs:** prohibited (including shield badges, typing
  graphics, hosted statistics, icons, streaks, decorative headers and footers).
- **Local visuals:** allowed only if present in the registered asset set; Phase 4 uses four static contribution variants.
- **External hyperlinks:** allowed where useful (GitHub, projects, LinkedIn,
  email), but must describe their actual destination.
- **Accessibility:** every meaningful image has alternative text; theme-specific
  source files must have an image fallback. The static SVGs include accessible names, while exact counts remain available
  as adjacent Markdown; actual assistive-technology testing on GitHub remains a manual publication check.

## Featured project prioritization

A featured entry qualifies only if it has a relevant problem statement, a
reachable repository or artifact, an explicit maturity classification, and
claims that can be linked to inspected evidence. **Selection and ranking is not
based on stars, GitHub activity heatmaps, the number of packages, or claimed
production readiness.**

Use the following editorial score **after inspecting a candidate's evidence**:

| Criterion | Weight | Scoring guidance (0–4) |
| --- | ---: | --- |
| Relevance to ML / research engineering | 35% | 0 = unrelated; 4 = directly illustrates intended ML/research engineering role |
| Demonstrated individual contribution | 25% | 0 = not attributable; 4 = independently inspectable code or technical authorship |
| Quality of verifiable evidence | 25% | 0 = unsubstantiated; 4 = runnable/reproducible tests, experiments and limitations |
| Implementation maturity | 15% | 0 = concept only; 4 = verified operational artifact appropriate to its scope |

Use the weighted average on a 0–100 scale. Do not fabricate scores: when a
project has not been inspected for a criterion, mark the score **unverified**
and postpone final evidence-based ranking. Formal reports are assessed as
research artifacts rather than falsely being measured as deployed services.

**Phase 3 evidence-informed editorial order (reviewed 2026-10-10):**

1. ASANAppeal AI — inspectable AI-workflow code, four labeled task datasets,
   evaluation routines and related tests; independent performance not rerun.
2. Bahar Operations — source-backed rule-based assessment and provenance
   controls; strong inspectable test coverage but baseline is explicitly
   editorial/untrained, with no field accuracy or regulatory qualification.
3. EO Drought Intelligence — directly relevant environmental/ML prototype
   with unit, integration and regression test sources; independent results
   and reproducible clean-environment installation remain unverified.
4. Neural Branch-and-Bound Accelerator — research/optimization report, not
   represented as a functioning or benchmarked software implementation.

The Personal Academic Website is retained as **additional engineering work**,
not a featured ML-oriented project. The 35/25/25/15 selection rubric remains
unchanged. No numerical editorial scores were assigned because individual
code authorship and representative empirical outcomes were not independently
established; the order is qualitative and explicitly evidence-limited. The
primary source references and qualification boundaries are in
`PROJECT_EVIDENCE.md`.

## Synchronization protocol

Whenever a change affects the profile contract, include these updates together:

1. Update `profile-spec.json` **first** (sections, assets, owner, project list).
2. Edit `README.md`, `CV.md` and `PROJECT_EVIDENCE.md` consistently with the spec; preserve verified facts and explicit evidence limitations.
3. Update scripts or workflows only where the manifest requires different
   sources or publication outputs; remove redundant generators.
4. Run `python3 scripts/validate_profile.py` and
   `python3 -m unittest discover -s tests -v` before committing.
5. Review the actual GitHub-rendered page after publishing, including links and
   assets. A local static check cannot guarantee GitHub rendering.
6. Record any architecture-policy decision change in this document.

A profile contract change should be submitted with its validator and tests in
one pull request. Automated generator commits must not mutate the contract or
manually maintained assets. CI's still-existing generation/freshness limitations
are intentionally part of the later CI/CD phase, not silently declared solved.

## Phase 1 verification checklist

- [x] Canonical machine-readable specification established.
- [x] Exactly one contribution/activity analytics representation retained.
- [x] Unused statistics workflow removed; missing outputs retired.
- [x] Remote image dependencies removed from the README.
- [x] Existing hero and ML system diagrams integrated in Phase 1; retired in Phase 4 after accessibility and relevance review.
- [x] Manually maintained and generated assets registered with owners.
- [x] Profile project editorial criteria defined; existing ordering justified.
- [x] README/validator/manifest change procedure documented.
- [x] Previous project descriptions and links retained for later evidence audit.


## Phase 2 — README validation contract (completed)

Phase 2 strengthens verification without changing the existing README project
claims, generated-calendar algorithm, or the Phase 1 publication architecture.
The repository uses a pinned CommonMark parser instead of scanning the raw
Markdown with regular expressions. Install the read-only validation dependency
before running local checks:

```bash
python3 -m pip install -r requirements-validation.txt
python3 scripts/validate_profile.py
python3 -m unittest discover -s tests -v
```

Both the profile-quality workflow and the calendar publishing workflow install
that dependency before validating the README. The full test suite includes the
original contract tests and the fixture-driven Phase 2 cases in
`tests/fixtures/profile_validation_cases.json`.

### Verified rules

- A real top-level level-2 Markdown heading must appear for every canonical
  section, in manifest order. Fenced-code examples, HTML comments and quoted
  headings are not counted as canonical sections.
- Markdown images (including reference-style images) and actual HTML `<img>`,
  `<source src>` and `<source srcset>` declarations are checked independently of
  HTML attribute order. Source candidates are checked separately.
- Only locally registered images in `assets/` or `profile/` may be embedded.
  Remote images and unregistered local images are rejected. Hyperlinks to other
  websites remain supported.
- Meaningful HTML and Markdown images require nonempty descriptive alternatives.
  A decorative HTML image must explicitly use `alt=""`, `role="presentation"`
  and `aria-hidden="true"` and cannot function as a link. `<picture>` requires an
  `<img>` fallback; its `<source>` elements inherit the fallback alternative.
- Live HTML uses the explicitly allowed tags in `profile-spec.json`. Code fences,
  inline code and comments may **mention** unsupported tags without making
  them part of the rendered document.
- Local file links must resolve inside the repository. README fragment links
  and fragment links to Markdown files must reference existing headings/IDs.
  Remote link liveness is not checked without a network request.
- Owned SVG assets must be valid SVG XML with positive finite dimensions and
  consistent viewBox geometry, an `img` role, nonempty linked title/description,
  unique IDs and safe local structure. XML DTD/entity declarations, executable
  script elements and event-handler attributes are not allowed.
- The manifest remains authoritative for asset ownership, output workflow,
  required image placement, featured-project identity, and section order.

### Extending the validator

1. Change the contract in `profile-spec.json` where it is a publication or
   component-policy decision.
2. Update the validator using the parsed Markdown/HTML representation rather
   than broad raw-source patterns.
3. Add at least one failing and one passing fixture where the rule allows it,
   and preserve all earlier fixtures.
4. Execute the two verification commands above before merging.
5. Confirm the actual GitHub presentation separately; static parsing does not
   establish layout correctness, color contrast, screen-reader behavior or the
   availability of external links.

**Remaining scope:** Phase 2 verifies document and asset contracts, not
contribution-API data validity, runtime freshness, full GitHub-rendering
accessibility, or concurrent workflow publication. Those remain separate later
phases and must not be considered fixed merely because the validator passes.


## Phase 3 — Professional content and evidence review (completed)

Phase 3 changes public-facing content and the manifest's featured-project
order, **not** the generator or publication workflows. The review covered the
public source trees for ASANAppeal, Bahar, EO Drought, DBMS Report, and Personal
Academic Website on **10 October 2026**. Source files, selected tests and
project-maintained documentation were inspected. No downstream repository was
installed, benchmarked or exercised with independent data as part of this review.

### Publishing contract

- The README begins with a short positioning statement and links directly to
  the CV, evidence index, primary projects, and professional contacts.
- Four ML/research-relevant featured projects retain visible, concise problem,
  implementation, outcome, maturity and limitations. All project evidence is directly visible under ordinary level-3 Markdown
  headings; no collapsible container controls its visibility.
- The projects are selected by the unchanged Phase 1 rubric; not ranked by
  repository stars, recentness, or architecture size. The website becomes
  correctly labeled additional source work, **not** a deployed website link.
- Evidence links reference the inspected source paths, tests, datasets,
  benchmark tooling, reports and appropriate setup instructions. Local CV and
  evidence-index links must exist and stay synchronized.
- The Bahar test count (`136 passed, 5 skipped`) is **repository-reported** from
  `docs/F49-F56_VERIFICATION_SUMMARY.md`, not independently re-executed.
  Neither this value nor test-source presence establishes domain accuracy.
- Authors' individual code contributions have not been attributed at line or
  commit granularity. Public language describes inspectable repositories and
  source evidence; no exclusive authorship is inferred.
- Academic degrees, honors, employment, model results, field outcomes and
  production-readiness assertions are omitted unless verified. Research
  interests are labeled as ongoing learning rather than achieved expertise.
- The `CV.md` is a conservative source-grounded in-repository technical CV; no
  separate resume URL is claimed to exist.

### Phase 3 checks

Run the unchanged Phase 2 validator and the complete suite after any portfolio
content change. The Phase 2 tests now include the two new Markdown documents in
isolated fixtures so cross-document links resolve. Additional Phase 3 tests
cover content order, maintained supporting documents, boundary language and
source-specific link identity. A successful local run does not establish the
continued live availability of the linked external repositories, or the actual
rendering behavior on GitHub.

## Phase 4 — Visual, accessibility and professional-content review (completed locally)

The README begins with semantic text identity, core project links and an H1.
Four featured projects use visible H3 headings and preserve their evidence and
limitations. The previous wide banner and method diagram were removed because
they duplicated content and reduced mobile legibility.

The contribution generator creates four **static** SVG outputs from the same
fetched calendar: desktop dark/light full-year grids and mobile dark/light
six-month numerical summaries. It also publishes a complete Markdown table of
monthly and daily counts (`profile/contributions-summary.md`). No CSS/SMIL motion
is used. This does **not** address Phase 5's input-schema and transactional
publishing weaknesses or Phase 6's scheduled-job/permission work.

The publication workflow now stages all five generated outputs, verifies
static SVG rendering using CairoSVG, and rechecks the README contract. The
quality workflow also runs visual smoke checks at representative viewport
widths. Read `VISUAL_REVIEW.md` for what was tested and what still requires a
real GitHub browser or assistive-technology review; read `LINK_REVIEW.md` for
linked GitHub evidence and the unverified LinkedIn destination; read
`CONTENT_REVIEW.md` for maintenance cadence and editorial update criteria.

Verified locally on 2026-10-10: registered assets, SVG XML and dimensions,
no motion elements, numerical summary parity, document links and content tests.
**No public GitHub deployment or browser-based screen-reader certification is
claimed.** Changes to project evidence remain outside this Phase 4 scope.


## Phase 5 — Contribution generation and publication (completed)

The contribution generator owns four static SVGs and the text-equivalent
`profile/contributions-summary.md` as a **single release set**. Only
`scripts/generate_contributions.py` may change those five generated files. The
README, project evidence, headings, and editorial content remain unchanged by
this scheduled workflow.

### Verified input contract

- The GraphQL `data.user.contributionsCollection.contributionCalendar` value
  must provide `totalContributions` and 1–54 ordered, nonempty `weeks`. Each
  week supplies a Sunday `firstDay` and 1–7 dated cells. Only partial edge
  weeks may be incomplete. There may be no duplicate dates or gaps.
- Every date is strict `YYYY-MM-DD`, and `weekday` is integer Sunday=0 through
  Saturday=6 and agrees with the date and `firstDay`. Counts and totals are
  nonnegative integers, not booleans; the sum of all daily counts equals
  `totalContributions`. Contribution levels are limited to GitHub's five
  named levels and must agree with whether daily count is zero.
- **Zero activity is not missing data.** A valid no-activity calendar includes
  explicit dated cells with zero counts and `NONE`. Missing or empty weeks,
  absent nested fields, GraphQL errors, or inconsistent values fail closed.
- Month labels are computed from visible dates, including year and partial
  month boundaries; short adjacent labels are spaced to avoid collisions. The
  exact reporting interval is always provided in the text table.

### API handling and provenance

- The generator attempts an HTTPS GraphQL request at most three times. It
  retries transient connection failures, 408/425/429/5xx responses, and
  explicitly rate-limited 403 responses. Waits are bounded to eight seconds,
  including `Retry-After`; permanent responses fail immediately. No token, raw
  response body, or sensitive header is copied into error messages.
- The response has a 2 MB cap. Invalid UTF-8, malformed JSON, partial
  GraphQL errors, and incomplete schemas are rejected rather than rendered.
- Each successful live retrieval writes the same UTC snapshot timestamp to
  the text report and the four SVG descriptions. **The inherited Phase 4
  snapshot has an unknown API retrieval time**, explicitly labeled in all
  five archived artifacts; do not substitute the current clock time for the
  missing historical observation. Displayed dates show the reporting interval.

### Publishing and recovery

- The source path is derived from the generator file's own repository root,
  not the caller's current directory.
- The generator validates the complete API dataset, produces all five candidate
  files, and checks SVG XML, accessible descriptions, totals, daily text counts,
  and consistent retrieval timestamps **before replacing anything published**.
- All candidates are staged in a temporary directory. The previous `profile/`
  directory is moved to a distinct backup under the repository root, and the
  candidate directory replaces it. Ordinary replacement failures trigger
  restoration. If restoration also fails, the backup path is preserved for
  manual recovery. Non-owned existing files are preserved in staging.
- This local replacement is **not a true atomic directory-exchange primitive**
  against power loss or simultaneous filesystem readers. The GitHub workflow
  commits all five verified paths together as one Git commit, so public Git
  readers see one commit rather than an intermediate mixture of assets.
- If a run fails, the workflow does not reach the Git commit step and the
  previously published snapshot remains unchanged. Scheduled runners can
  still fail or be delayed; keep the GitHub live-activity link as the fallback.

### Reproducible offline verification

```bash
python3 -m pip install -r requirements-validation.txt -r requirements-visual.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_profile.py
python3 scripts/check_visuals.py
```

The Phase 5 tests simulate valid/invalid GraphQL data, zero activity, leap
days, year transitions, invalid weekdays and levels, total mismatches, 403/503
and network retries, oversized/malformed responses, both theme variants,
filesystem independence, and a publication failure with rollback. No external
API calls, credentials, or production model benchmarks are needed for these
tests. A **live** GitHub update is not established by local success.

## Phase 6 — CI/CD, least privilege, and publication closure (2026-10-10)

**Precedence:** This section supersedes earlier notes describing a single-job generator with write credentials. The Phase 1–5 design and all user/project content remain unchanged.

1. **One publisher and exact ownership.** Only `update-contributions.yml` is authorized to propose changes to the four SVGs and the text summary. `scripts/profile_release.py` defines the same five-file allowlist for the candidate, extracted files, staging, and Git commit. The quality workflow is independent and read-only.
2. **Immutable dependencies.** Official `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, and `actions/download-artifact` are pinned to exact reviewed 40-character SHA commits (tag references appear only as comments). Other workflows use the same SHA pinning discipline.
3. **Separated jobs.** Generation is read-only, without persisted checkout credentials. Only the narrowly scoped `publish` job has `contents: write` / `pull-requests: write`. No third-party statistics generator is executed with repository write rights.
4. **Handoff boundary.** Generation independently validates GraphQL data, every output, project policy, and SVG raster; it produces a candidate ZIP with source SHA, snapshot provenance, and five SHA-256 records. Publication inspects the ZIP for unwanted paths, corrupt bytes, stale timestamps, and incoherent SVG/summary content before touching the Git worktree.
5. **Conflict discipline.** Publisher fetches current main and refuses to apply a candidate based on changed README/spec/generator/validator/workflow/registered assets. On benign concurrent repository changes it applies candidate to the new tip and reruns the complete checks. The push is fast-forward only and uses a bounded three-attempt retry; never rewrite the main branch.
6. **Protected branch behavior.** A rejected direct push may fall back to an automation branch and reviewable PR, if workflow permissions allow. The workflow explicitly reports **not yet published on main**. `GITHUB_TOKEN` PRs may not trigger normal CI automatically; a manual quality dispatch/check and human merge may be required. Branch protection details were inaccessible via connected integration (403), so no live bypass or branch-protection clearance is asserted.
7. **Public verification.** On direct publication, the publisher confirms public main's tip, verifies immutable public commit files, the five-file count/provenance/freshness contract, and the presence of key project names in the public GitHub profile HTML. On normal main pushes, the quality workflow checks public source and HTML presence. Actual browser layout and screen-reader functionality remain manual obligations in `PUBLICATION_RUNBOOK.md`.
8. **Recovery and observability.** Job summaries distinguish `direct-main`, `pull-request`, and `unchanged` results; errors fail the job. Rejected/corrupted candidates leave main unchanged. Incorrect published artifacts are recovered by reviewed Git revert, not force push. A dated review checklist and operator commands live in `PUBLICATION_RUNBOOK.md`.

**Verified locally:** Source-level README checks, previous Phase 1–5 regression suite, new bundle-integrity tests, isolated Git fast-forward and protected-push simulations, YAML syntax parsing, and responsive SVG raster checks. **Not verified live:** job execution on GitHub hosted runners, credential/policy settings, actual publishing or merging, UI/browser rendering, remote API availability, or assistive-technology accessibility.
