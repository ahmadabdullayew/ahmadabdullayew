# Project evidence and verification index

**Review date:** 10 October 2026  
**Scope:** Public GitHub repository trees, selected source files, test directories, project READMEs, and technical documentation were inspected for the profile's Phase 3 content review. **No downstream repository test suite, model benchmark, deployed service, or production integration was independently executed.** A source file's presence is evidence that code exists; it is not proof of its runtime effectiveness. Repository ownership alone is not proof that the profile owner personally authored each line.

## Evidence and maturity matrix

| Project | Problem / approach | Inspectable implementation and reproduction entry | Observed or reported outcome | Qualification boundary |
| --- | --- | --- | --- | --- |
| **[ASANAppeal AI](https://github.com/ahmadabdullayew/Asan-Appeal)** | Civic-AI intake, routing, drafting and verification; explicit human-review paths | [Evaluation code](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/app/evaluation.py), [four task datasets](https://github.com/ahmadabdullayew/Asan-Appeal/tree/main/data/evals), [evaluation tests](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/tests/test_evaluation.py), [run instructions](https://github.com/ahmadabdullayew/Asan-Appeal#run-locally) | Source-available runnable-backend *foundation* with evaluation and test entry points | No independently reproduced evaluation score, external production use, or individual line-level authorship audit |
| **[Bahar Operations](https://github.com/ahmadabdullayew/Bahar)** | Evidence-governed recipe/label inconsistency screening; deterministic baseline with human authority | [Engine](https://github.com/ahmadabdullayew/Bahar/blob/main/src/bahar_ai_core/engine.py), [operations code](https://github.com/ahmadabdullayew/Bahar/tree/main/src/bahar), [test suite](https://github.com/ahmadabdullayew/Bahar/tree/main/tests), [demo video](https://github.com/ahmadabdullayew/Bahar/blob/main/demo/bahar-demo.mp4), [setup](https://github.com/ahmadabdullayew/Bahar#run-the-full-localhost-system) | [Oct 2026 report](https://github.com/ahmadabdullayew/Bahar/blob/main/docs/F49-F56_VERIFICATION_SUMMARY.md) states **136 passed, 5 skipped** in its reported environment; **not independently reproduced** | Baseline is untrained, reference data editorial; field recall, regulatory qualification, production SSO, and full real-DB integration unverified |
| **[EO Drought Intelligence](https://github.com/ahmadabdullayew/EO-Drought-Intelligence)** | Environmental-data and EO prototype; processing, analytics, ML modules | [Source](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/eo_drought); [unit](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/unit), [integration](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/integration), [regression](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/regression) tests | Inspectable hackathon prototype source with tests organized by purpose | No independent drought prediction benchmark, irrigation-outcome measurement, or verified clean installation; dependencies manifest includes an unfinished placeholder |
| **[Neural Branch-and-Bound Accelerator](https://github.com/ahmadabdullayew/DBMS-Report)** | Formalize learning-guided exact physical design with deterministic acceptance of proposals | [PDF report](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/docs/DBMS.pdf), [README](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/README.md) | Available technical/research report describing formulation, exactness constraints, and an evaluation plan | No executable solver, independent proof review, or observed speedup established by the inspected repository |
| **[Personal Academic Website](https://github.com/ahmadabdullayew/personal-academic-website)** | Traceable engineering foundation for a personal website | [Source](https://github.com/ahmadabdullayew/personal-academic-website/tree/main/src), [tests](https://github.com/ahmadabdullayew/personal-academic-website/tree/main/tests), [local setup](https://github.com/ahmadabdullayew/personal-academic-website#local-setup) | Source and development/test commands exist; treated as *additional* SWE work | GitHub source is not proof of a publicly deployed academic website or production environment |

## Research and evaluation maturity

| Research/evaluation dimension | ASANAppeal | Bahar | EO Drought | Neural Branch-and-Bound |
| --- | --- | --- | --- | --- |
| Question / intended task | Route/review civic submissions | Investigate recipe-label mismatches | Estimate drought stress / irrigation priority | Guide exact database design search |
| Approach | Service-oriented task evaluation | Deterministic lexical baseline with evidence gates | EO / environmental processing and ML modules | Formal exact optimization with advisory learned proposals |
| Baseline evidence | Gold-style tasks, acceptance-gate implementation | Untrained editorial baseline explicitly documented | Prototype components; no independently verified field baseline | Formulation and benchmark plan; no verified executable comparator |
| Reproduction entry point | Local setup, `pytest`, `app/evaluation.py` | Local setup, `pytest`, benchmark scripts | Code and test directories; clean environment not independently validated | Report PDF only |
| Measured result | **Not independently reproduced** | **136 passed / 5 skipped documented, not reproduced**; no field-accuracy result | **Not independently reproduced** | **No measured speedup established** |
| Limitations | Domain/generalization, deployment | Scientific corpus validation, multilingual coverage, production identity/regulatory qualification | Dataset quality, actual field outcomes, dependency reproducibility | Formal review, implementation, experiments |

## Skills and source traceability

| Skill or method | Supporting source | What the source supports — and does not |
| --- | --- | --- |
| Python service decomposition | [ASANAppeal app](https://github.com/ahmadabdullayew/Asan-Appeal/tree/main/app) | Implemented modules; not independent backend-scale/performance validation |
| Task-level evaluation and calibration code | [ASANAppeal evaluation.py](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/app/evaluation.py) | Task metrics/threshold-search implementation; not demonstrated predictive quality |
| Deterministic data / rule logic | [Bahar engine](https://github.com/ahmadabdullayew/Bahar/blob/main/src/bahar_ai_core/engine.py) | Source-grounded baseline; **not** a trained model |
| Provenance and review architecture | [Bahar code](https://github.com/ahmadabdullayew/Bahar/tree/main/src/bahar), [documented limits](https://github.com/ahmadabdullayew/Bahar/blob/main/docs/F49-F56_VERIFICATION_SUMMARY.md) | Scoped implementation and explicitly pending qualification |
| ML pipeline organization | [EO Drought ML modules](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/eo_drought/ml), [tests](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests) | Module structure and test code, not field validity or scientific performance |
| Optimization / research writing | [DBMS technical report](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/docs/DBMS.pdf) | Proposed formal design and evaluation protocol, not a benchmarked implementation |
| Django / TypeScript platform tooling | [Academic website source](https://github.com/ahmadabdullayew/personal-academic-website) | Extra general SWE work; separate from ML-specialization claims |

## Individual contribution and authorship boundary

The repository paths above provide a concrete and inspectable **project-level** description. This content review did not establish a comprehensive, author-by-author attribution for specific algorithms, code modules, datasets, or research passages. Therefore the public profile **does not claim sole authorship** of individual components. Specific contributions can be added when linked to commit history, an accepted project contribution record, or other attributable evidence. Do not infer personal credit from repository ownership alone.

## Evidence maintenance procedure

1. Recheck each featured repository's linked files before changing an implementation claim.
2. For numerical outcomes, record the exact dataset, test command, version/commit, date, environment and source of the measurement; distinguish **reported** from **independently reproduced** results.
3. Reassess maturity separately from architectural ambition. An implementation foundation is not a deployed service; a report is not an executable benchmark.
4. Replace stale links or remove unsupported claims promptly. Keep this review date distinct from the latest GitHub contribution snapshot date.
5. Update the README, CV, this index, `profile-spec.json`, and relevant tests in the same change when featured projects or evidence-level claims change.
