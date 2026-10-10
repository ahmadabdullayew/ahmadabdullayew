# Link destination review — Phase 4

**Review date:** 2026-10-10. **Evidence scope:** Archived Phase 3 repository and verified public GitHub paths inspected through the connected GitHub repository interface. Local links and fragments were also checked by the repository's Phase 2 validator.

| Destination group | Status | Evidence |
| --- | --- | --- |
| ASANAppeal AI | Verified repository and referenced file/directory paths | `app/evaluation.py`, `tests/test_evaluation.py`, `app/`, `data/evals/`, `tests/`, README |
| Bahar Operations | Verified repository and referenced file/directory paths | `src/bahar_ai_core/engine.py`, `src/bahar/`, `scripts/benchmark_f28_f38.py`, `docs/` files, `tests/`, `demo/`; `demo/bahar-demo.mp4` exists in `demo/` directory listing |
| EO Drought Intelligence | Verified referenced code and test directories | `eo_drought/`, `eo_drought/ml/`, and `tests/{unit,integration,regression}` |
| DBMS Report | Verified report repository and `docs/` directory | `docs/DBMS.pdf` exists in `docs/` listing. PDF contents were not re-audited in this phase |
| Personal Academic Website | Verified repository and source/test paths | `src/`, `tests/`, README; linked as source code rather than a deployed site |
| GitHub user overview | URL is well-formed | Public profile's rendered query/tab interface was not verified in a browser |
| LinkedIn profile | **Unverified** | Direct fetch was blocked by the access environment. Preserve current link, check manually after publication; do not label it broken without contrary evidence |
| Email (`mailto:`) | Syntax checked locally | Deliverability and mailbox ownership cannot be established by a static profile audit |
| README / CV / evidence index / contribution summary | Validator passed | Local file references and Markdown fragments resolve inside the ZIP |

**Limitations:** A successful GitHub repository-path lookup proves the file/directory existed at review time, not that it will remain available. This review is not a continuous external-link monitor. API validation and live browser navigation differ. If links begin returning 404, change the README and evidence index together after confirming the intended replacement.

## Ongoing verification

1. On important project publication or quarterly content review, test all README, CV and evidence-index links.
2. Check that every GitHub link still targets its intended repository, branch, file, folder, anchor, or video.
3. Manually check LinkedIn, email, and the live GitHub contributions link in an actual browser.
4. Treat rate limits, login walls, anti-bot blocks, and network errors as **unverified**, not as broken links.
5. Record review date, failures, repairs, and any intentionally deferred destinations.
