# Ahmad Abdullayev

**Computer Engineering student at Khazar University · Python/ML engineering and research-oriented software · Baku, Azerbaijan**

I build inspectable AI workflows, evaluation code and data-processing prototypes. The strongest public evidence is in [ASANAppeal AI](https://github.com/ahmadabdullayew/Asan-Appeal) and [Bahar Operations](https://github.com/ahmadabdullayew/Bahar); project maturity and independent-verification limits are stated below.

[Featured projects](#featured-projects) · [Project evidence](./PROJECT_EVIDENCE.md) · [Technical CV](./CV.md) · [GitHub](https://github.com/ahmadabdullayew) · [Contact](#connect)

## About

My interests center on reliable machine-learning systems, evaluation, and the mathematics of computer vision and autonomous systems. The public projects below contain source code, tests or a formal technical report; **their availability does not establish production deployment, independent model accuracy or individual authorship of every file**.

## Featured Projects

The entries are ordered by **ML/research-engineering relevance, inspectable implementation, evidence quality, and maturity**, not by project size or recency. Descriptions below refer to repository artifacts reviewed on **10 October 2026**. Repository ownership does not, by itself, prove individual authorship of every file.

### ASANAppeal AI — Civic-AI workflow with inspectable evaluation

**Problem:** Structure submitted complaints, route them to relevant institutions, and support drafting and verification without treating uncertain automated decisions as final.

**Inspectably implemented:** A Python/FastAPI backend containing intake, routing, priority, drafting and review services; a local execution option; evaluation code and four gold-style task datasets. The [evaluation implementation](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/app/evaluation.py) includes task metrics, acceptance gates, and threshold candidates; [evaluation tests](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/tests/test_evaluation.py) exercise that path.

**Outcome and limit:** A source-available, testable backend foundation; **no independently reproduced accuracy, calibration score, or production deployment is claimed**. Individual code authorship has not been confirmed from a contribution audit.

**Reproduce / inspect:** [Repository](https://github.com/ahmadabdullayew/Asan-Appeal) · [Local setup](https://github.com/ahmadabdullayew/Asan-Appeal#run-locally) · [Tests](https://github.com/ahmadabdullayew/Asan-Appeal/tree/main/tests) · [Evaluation datasets](https://github.com/ahmadabdullayew/Asan-Appeal/tree/main/data/evals)


### Bahar Operations — Evidence-governed recipe-to-label assessment

**Problem:** Detect and investigate potential inconsistencies between recipes, ingredient information, and food labels while keeping evidence, technical findings, and human release decisions separate.

**Inspectably implemented:** A local application with a [deterministic lexical engine](https://github.com/ahmadabdullayew/Bahar/blob/main/src/bahar_ai_core/engine.py), [assessment and governance code](https://github.com/ahmadabdullayew/Bahar/tree/main/src/bahar), [automated tests](https://github.com/ahmadabdullayew/Bahar/tree/main/tests), and a [local demonstration](https://github.com/ahmadabdullayew/Bahar/blob/main/demo/bahar-demo.mp4).

**Outcome and limit:** The repository documents a cumulative local test run of **136 passed, 5 skipped** in its [verification report](https://github.com/ahmadabdullayew/Bahar/blob/main/docs/F49-F56_VERIFICATION_SUMMARY.md). This is a **repository-reported result, not independently reproduced here**. The baseline is editorial and **untrained**, not an independently validated ML classifier, food-safety authority, or certified production system.

**Reproduce / inspect:** [Repository](https://github.com/ahmadabdullayew/Bahar) · [Local setup](https://github.com/ahmadabdullayew/Bahar#run-the-full-localhost-system) · [Input/AI limitations](https://github.com/ahmadabdullayew/Bahar/blob/main/docs/F28-F38_INPUT_AI_REMEDIATION.md) · [Frontend verification](https://github.com/ahmadabdullayew/Bahar/blob/main/docs/FRONTEND_IMPLEMENTATION_AND_VERIFICATION.md)


### EO Drought Intelligence — Environmental-data and ML pipeline prototype

**Problem:** Explore drought stress and irrigation prioritization from earth-observation and environmental signals.

**Inspectably implemented:** A Python project with data processing and ML module boundaries, plus [unit](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/unit), [integration](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/integration), and [regression](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests/regression) test sources.

**Outcome and limit:** A source-available **hackathon prototype**, not an independently validated agricultural prediction service. This review did not reproduce field-level model performance, irrigation savings, or a complete fresh-environment installation.

**Reproduce / inspect:** [Repository](https://github.com/ahmadabdullayew/EO-Drought-Intelligence) · [Code](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/eo_drought) · [Tests](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/tests)


### Neural Branch-and-Bound Accelerator — Learning-augmented optimization study

**Research question:** How can learned proposals guide database physical-design search without becoming an authority for exact pruning and correctness?

**Artifact:** A [formal technical report (PDF)](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/docs/DBMS.pdf) describing mixed-integer formulation, exact-search mechanisms, deterministic acceptance boundaries, and an evaluation protocol.

**Outcome and limit:** The available repository supplies a **written research/technical artifact**, not a verified executable optimizer. No measured solver speedup, completed baseline comparison, or independently reviewed proof is claimed here.

**Inspect:** [Report repository](https://github.com/ahmadabdullayew/DBMS-Report) · [Report PDF](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/docs/DBMS.pdf)


**Additional engineering work:** [Personal Academic Website — source repository](https://github.com/ahmadabdullayew/personal-academic-website). It documents a web-platform implementation foundation and local quality commands; **this link is not a deployed website**. Its lower prominence reflects the profile's ML/research-engineering focus, not a claim that the project is less rigorous.

## ML Experience and Research

| Category | Supported work | Evidence or boundary |
| --- | --- | --- |
| **Implemented / inspectable** | Python services, rule-based evaluation, test suites, structured data processing | [ASANAppeal](https://github.com/ahmadabdullayew/Asan-Appeal/tree/main/app), [Bahar](https://github.com/ahmadabdullayew/Bahar/tree/main/src), [EO Drought](https://github.com/ahmadabdullayew/EO-Drought-Intelligence/tree/main/eo_drought) |
| **Evaluation practice in source** | Labeled test examples, acceptance conditions, regression checks, reporting and documented limitations | [ASANAppeal evaluation](https://github.com/ahmadabdullayew/Asan-Appeal/blob/main/app/evaluation.py), [Bahar benchmark tooling](https://github.com/ahmadabdullayew/Bahar/blob/main/scripts/benchmark_f28_f38.py) |
| **Research / formal study** | Exact optimization, learning-augmented search and evaluation methodology | [Database design report](https://github.com/ahmadabdullayew/DBMS-Report/blob/main/docs/DBMS.pdf); no verified experimental speedup |
| **Ongoing learning** | Proof-based mathematics, probability, optimization, computer vision, reinforcement learning and autonomous systems | Learning direction, **not** an assertion of demonstrated research results |

**Engineering approach:** Define the decision and risks, build a baseline, validate outcomes, calibrate uncertainty where appropriate, integrate carefully, and monitor limitations. This is a working principle, **not evidence that every project has completed every stage**.

## Technical Foundation

**Most directly evidenced:** Python, data processing, test automation, HTTP services, local persistence, structured rule evaluation, and Git-based source control. Inspect the [project-to-skill evidence matrix](./PROJECT_EVIDENCE.md#skills-and-source-traceability) for specific supporting repositories and files.

**Project-specific tools:** FastAPI, SQLite, SQLAlchemy, NumPy and scikit-learn appear in the relevant repository code or manifests. A listed dependency is **not** a proficiency certification. The [academic website source](https://github.com/ahmadabdullayew/personal-academic-website) additionally demonstrates Django/TypeScript-oriented platform work.

## GitHub Activity

This is a **static snapshot** of public GitHub contributions, not a measure of engineering ability. [Read the accessible date-and-count table](./profile/contributions-summary.md) or [view live contributions on GitHub](https://github.com/ahmadabdullayew?tab=overview). The snapshot can become stale if scheduled generation fails.

<p align="center">
  <a href="https://github.com/ahmadabdullayew?tab=overview">
    <picture>
      <source media="(max-width: 640px) and (prefers-color-scheme: dark)" srcset="./profile/contributions-mobile-dark.svg" />
      <source media="(max-width: 640px)" srcset="./profile/contributions-mobile-light.svg" />
      <source media="(prefers-color-scheme: dark)" srcset="./profile/contributions-dark.svg" />
      <img src="./profile/contributions-light.svg" alt="Static GitHub activity chart. See the adjacent accessible activity summary for numerical counts and reporting dates." width="100%" />
    </picture>
  </a>
</p>

## Current Focus

**Building:** Reviewable AI tools, reproducible evaluation, reliable Python systems. **Learning:** Mathematics, computer vision, reinforcement learning, and robotics/autonomous systems. **Seeking:** ML/AI engineering internships, research-oriented collaborations, and rigorous open-source work.

## Connect

[Technical CV](./CV.md) · [Project evidence index](./PROJECT_EVIDENCE.md) · [GitHub](https://github.com/ahmadabdullayew) · [LinkedIn](https://www.linkedin.com/in/ahmad-abdullayev-826816289/) · [Email](mailto:ehmedmanafoghlu@gmail.com)
