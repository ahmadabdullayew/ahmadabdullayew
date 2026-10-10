# Profile UI/UX review — 10 October 2026

## Design source and interpretation

The user-selected [Awesome GitHub Profile README](https://github.com/abhisheknaiidu/awesome-github-profile-readme) is a **curated reference index**, not an application template or a license to copy another author's profile. We reviewed its **Minimalistic**, **Descriptive**, and **Simple but Innovative Ones** collections, with reference implementations including [Caneco](https://github.com/Caneco/Caneco), [rednafi](https://github.com/rednafi/rednafi) and [Simon Willison](https://github.com/simonw/simonw).

We adopt *patterns*, not their language, images, icons, code, or identity:

1. **Identity before ornament:** owner name, discipline, evidence-led specialization; no image obscures the first screen.
2. **Useful navigation:** projects, independent evidence index, CV, and contact exposed immediately.
3. **Scannable project sections:** visible level-three headings, a restrained inline technology line, and consistent problem / implementation / outcome / reproduction paths.
4. **Evidence first:** distinguish independently unverified claims from repository-reported tests; no inflated badges or production claims.
5. **Native GitHub rendering:** plain Markdown and simple typography for both themes and narrow screens, without cards, HTML tables, animated typing or remote icon services.
6. **Owned graphics only:** keep existing responsive contribution SVGs and the equivalent Markdown counts; link to live GitHub contribution activity to make staleness transparent.

## Layout decisions and non-goals

- Profile content is a technical portfolio, not a trophy wall or statistics dashboard.
- No externally hosted counters, follower/streak badges, remote GIFs, rotating banners, embedded third-party typing or additional service dependencies.
- No publication of unverified job titles, experimental outcomes, solver performance or live website claims.
- The 7 primary README sections, ordered project titles, 4 theme/responsive SVG assets, and Phase 1–6 policies remain unchanged.
- The README is deliberately condensed; technical details stay in `PROJECT_EVIDENCE.md` and `CV.md`.

## Acceptance checks

- The first screen contains name, professional specialization, four primary project links, evidence index, and CV.
- All featured projects are plainly visible, keyboard-navigable GitHub headings with reproduction links.
- The repository validator and full previous-phase regression suite pass.
- No unregistered image, third-party embedded image, animation, or hidden project panel.
- Static checks do **not** replace a real GitHub light/dark desktop/mobile and screen-reader review after publication; follow `VISUAL_REVIEW.md`.

## Known separate publication defect

As of the reference review, `main`'s **public verification** step failed because the verifier read a truncated GitHub commit API response. That is an independently scoped CI repair, not a presentation defect. A publishing branch should address or include the minimal fix before release so the merge does not leave `main` red.
