# CAUSATRACE
## Evidence-Verified, Uncertainty-Aware Root Cause Analysis for Distributed Software Systems

**Project design notes**
**Version:** 1.0 — 6 November 2026  
**Status:** Initial design. See the [roadmap](ROADMAP.md) for current progress.

> **One-sentence project statement:** CausaTrace investigates incidents in distributed software systems, ranks possible root causes from operational telemetry, checks the evidence for and against each explanation, and either produces an auditable incident report or explicitly states what additional evidence is needed.

> **Mission:** Reduce the time and effort required to diagnose complex software incidents **without** giving engineers unwarranted confidence in unsupported AI explanations.

---

## 1. Executive summary

CausaTrace is an open-source **AIOps / AI engineering / applied ML** platform for incident investigation. Its inputs are time-series performance metrics, application logs, optional distributed traces, optional service-dependency graphs, and an incident time window. Its outputs are a ranked shortlist of likely root causes, supporting and contradicting observations with precise provenance, a calibrated confidence or uncertainty indicator when justified, a recommended next diagnostic check, and an exportable report. It **never claims that a statistical association establishes causation**.

The product is designed for site reliability engineers (SREs), DevOps teams, platform engineers, IT operations analysts, incident responders, and ML researchers evaluating root cause localization. The beneficiaries are teams responsible for reliable digital services and, indirectly, users who depend on those services.

This is **not** a simple LLM wrapper over logs. Traditional statistical/ML techniques perform evidence retrieval and service ranking; a controlled investigator examines candidate explanations; an independent verification process checks whether claims are grounded; and an uncertainty/abstention policy prevents overconfident reports. The application will be an **end-to-end, reproducible GitHub project**, usable without a paid API or access to a production cluster.

### What success looks like

A new user can clone the repo, run a documented demo locally, open a dashboard, select an included sample incident, inspect suspect services and cited telemetry, run a deterministic diagnosis, and download a report. After separately downloading a public benchmark, they can reproduce comparative evaluations. A hosted demo may be added later, but **local reproducibility is mandatory**.

---

## 2. Problem, users, and value

**Problem:** A failure in one service may cause errors and latency in several downstream services. Engineers must piece together telemetry from different sources to distinguish an originating problem from its symptoms. Generic AI assistants may describe plausible but unsubstantiated explanations, while standalone anomaly detectors often identify unusual data without explaining its operational relevance.

**Who uses it:** SRE/DevOps/platform teams, incident managers, engineering students, and applied-ML researchers.

**Benefits to test, not to assume:** Faster root-cause triage; fewer unsupported conclusions; clearer escalation and handoff; better prioritization of what to inspect next; and reproducible comparisons across RCA algorithms. Measure these benefits in experiments or controlled user tasks before claiming actual improvements.

**Scope:** Historical, replayed, and locally simulated incidents in distributed/microservice environments. **Out of scope for v1:** automated modification of production systems, destructive remediation, production incident guarantees, security penetration testing, and real-time claims about live infrastructure without a verified ingestion path.

---

## 3. Differentiating contribution: EvidenceGap

**Proposed signature feature: EvidenceGap — counter-hypothesis testing + actionable evidence-gap discovery.** Rather than outputting one persuasive cause, CausaTrace should:

1. Produce **at least two competing root-cause hypotheses** when there are plausible alternatives.
2. Build a **claim–evidence graph**: each important assertion links to timestamped metrics, log rows, trace spans, or a documented dependency edge. Every cited item must be retrievable.
3. Label observations as **supporting, contradicting, missing, or ambiguous**, instead of treating all retrieved text as supporting evidence.
4. Run a **counter-hypothesis challenge**: identify evidence that weakens the top candidate, check whether the same symptom can be explained by a downstream cascade, and compare against a second candidate.
5. Choose a **minimum-cost discriminating next check** when evidence is insufficient: e.g., “inspect database connection-pool saturation in the 2 minutes before the first timeout,” not “check the logs.” This recommendation must identify the signal, service, time range, purpose, and availability, and must not imply unavailable telemetry exists.
6. **Abstain or return ‘needs investigation’** when evidence is too weak, contradictory, missing, or out of distribution. Do not manufacture numerical certainty.
7. Preserve an **audit trail** that can reconstruct why the top hypothesis was selected, which candidate was rejected, what was missing, and which tools were called.

### Why this can stand out

The distinctive combination is **root-cause ranking + explicit counter-evidence + evidence-gap recommendations + selective prediction/abstention + reproducible evaluation** in one open-source product. These ideas overlap with existing RCA, agentic, calibration, and evidence-grounding literature. **Do not claim this combination is globally novel or first-of-its-kind without a systematic literature review.** The contribution must be established by a defined method, ablations, and measured trade-offs.

### Testable research hypothesis

> Compared with a baseline that chooses the most likely root cause without cross-checking contradictory evidence, EvidenceGap can reduce unsupported incident reports and improve selective diagnostic accuracy at a controlled abstention rate, while remaining practical in runtime and cost.

This is a **hypothesis**, not an expected or promised result. Record negative findings honestly.

### EvidenceGap evaluation (required)

- **Correct localization:** Top-1 / Top-3 root-cause service accuracy, optionally root-cause indicator and fault-type accuracy where annotated.
- **Evidence fidelity:** fraction of cited references that exist and actually support the claim; human- or rubric-reviewed contradiction handling; unsupported-claim rate.
- **Selective reliability:** accuracy on answered cases versus **coverage** (fraction not abstained on); risk–coverage curves, AURC where appropriate; abstention quality on ambiguous/perturbed examples.
- **Discriminating checks:** percentage of proposed checks that are feasible, relevant and capable of separating the top two hypotheses (using a labeled or manually reviewed subset).
- **Efficiency:** time per incident, token use and API cost (if LLM mode is enabled).
- **Ablations:** without graph information; without counter-hypothesis challenge; without evidence-grounding verification; without abstention; no LLM.

Crucial methodological note: RCA benchmarks do not necessarily label all supporting/contradicting evidence or the best next check. Create a **small, explicitly identified, reviewed evaluation set** with transparent annotation rules for these secondary metrics; do **not** present inferred annotations as benchmark ground truth.

---

## 4. Data plan — real sources, not invented data

### Primary benchmark: RCAEval (recommended)

- **Source and code:** https://github.com/phamquiluan/RCAEval
- **Dataset hub:** https://huggingface.co/datasets/phamquiluan/RCAEval
- **Archive/citation:** https://zenodo.org/records/14590730
- **What is available:** 735 annotated failure cases across three microservice systems (Online Boutique, Sock Shop, Train Ticket), organized in RE1/RE2/RE3 benchmark suites, 11 fault types overall. Per-case annotations include root-cause service and root-cause indicator. RE1 is metrics-focused; RE2 and RE3 provide multimodal telemetry for applicable cases (metrics/logs, and traces when supplied).
- **Size/access:** Hugging Face Parquet representation is approximately 3.4 GB in total and supports selecting individual suites/cases. Start with a small subset rather than cloning the entire data collection.
- **Use:** RE1 for fast baseline experiments; **RE2** for full metric–log–trace investigation (confirm trace availability on each selected system); RE3 for transfer/generalization tests when suitable.
- **Important:** Faults are benchmark/experiment cases, **not a sample of arbitrary production outages**. Do not promise performance on live incidents.

### Secondary smoke test: OpenStack-RCA-Bench

- **Dataset:** https://zenodo.org/records/20136820
- **Research description:** https://conf.researchr.org/details/ase-2026/ase-2026-tools-and-data-sets/58/OpenStack-RCA-Bench-A-Reproducible-IaaS-Root-Cause-Analysis-Dataset
- **What is available:** 64 chaos-engineering incidents, structured logs and injected-fault ground truth, about 145,133 log lines per the research description. Downloaded archive roughly 9.7 MB.
- **Use:** optional lightweight second-domain evaluation or smoke-test adapter, **not** a direct replacement for metric–log–trace evaluation.
- **Caveat:** Published rule-based baseline is already strong (~92% F1 overall). Do not cherry-pick comparisons or imply that a sophisticated agent must beat it.

### Stretch benchmark: OpenRCA

- **Source:** https://github.com/microsoft/OpenRCA
- **Overview:** https://microsoft.github.io/OpenRCA/
- **What is available:** 335 failures with logs, metrics and traces; over 68 GB of telemetry. The repository recommends at least 80 GB storage and 32 GB RAM for the full environment.
- **Use:** stretch validation only, **not a hard dependency** or default quickstart.

### Data governance and reproducibility requirements

- **First action:** inspect dataset cards, file formats, accessibility, usage license/terms, and citation requirements; record exact sources and revisions in `docs/DATASETS.md`. **Public availability does not automatically mean redistribution is permitted.**
- Never commit multi-GB datasets, third-party archives, secrets, production logs, personal information, or API keys to Git. Use `.gitignore` for `data/raw/`, caches, environment files, model binaries, and run outputs.
- Create `scripts/download_data.py` to fetch **only requested** public benchmark cases/splits with checksum/provenance where available, helpful failures, and documented disk estimates. Do not silently fetch gigabytes during setup.
- Create a small **self-authored, explicitly synthetic** fixture set under `data/demo/` for an immediate offline demo. Include ground-truth labels only for tests, never expose them to the investigator during inference.
- Treat missing traces/dependency graphs honestly: mark them absent and switch to a documented degraded mode; never fabricate edges or observations. Derive topology from trace spans only if trace data supports it, and label inferred edges.
- Split by **incident/failure case, system/scenario and repeated fault-injection group** as feasible; prevent leakage from adjacent time windows, shared incident IDs, or derived features. Evaluate transfer to held-out services, fault types, or systems as an explicit generalization experiment where the dataset allows.
- Preserve source incident IDs, timestamps, units, fault-injection metadata and label maps, with consistent normalization schemas and missingness masks.

---

## 5. Product capabilities and user workflow

### Essential v1 features

1. **Incident browser:** select a sample or downloaded benchmark incident; inspect time window and telemetry availability.
2. **Telemetry explorer:** plot metrics with fault window, search/filter log messages, view traces where available, and inspect service graph.
3. **Candidate ranking:** return top suspects, score components and linked observations; clearly distinguish anomaly scores from calibrated probabilities.
4. **Evidence ledger:** stable references such as `incident_id/source/service/timestamp/row_id`; clickable evidence with source context.
5. **EvidenceGap workspace:** side-by-side competing hypotheses, supporting/contradicting/missing evidence, best next check, abstention state and explicit reasons.
6. **Report export:** structured JSON and human-readable Markdown (PDF optional), including dataset/source IDs, model version, evaluation status, known limitations and decision trace.
7. **Evaluation lab:** reproduce baselines and ablations from a CLI without a cloud subscription.
8. **Offline operation:** baseline diagnosis and demo run entirely without an LLM key. Optional LLM mode is a clear opt-in.

### Optional v2 features

- A read-only tool-using LLM investigator that queries **bounded** telemetry slices rather than receiving all logs at once; structured outputs validated against a schema.
- Confidence calibration or conformal/selective prediction **only with sufficient validation data and documented assumptions**.
- Human feedback on whether evidence is persuasive; export review annotations.
- Scenario-replay animation showing how an incident unfolds over time.
- Read-only alert/webhook integration in a sandbox, with synthetic sources and no autonomous remediation.

### Example output (illustrative, not a real result)

```json
{
  "incident_id": "demo-002",
  "status": "NEEDS_INVESTIGATION",
  "top_hypotheses": [
    {
      "service": "orders-db",
      "reason": "Connection errors precede upstream timeouts",
      "supporting_evidence_ids": ["log:orders-db:0017", "metric:orders-db:conn_errors:20"],
      "contradicting_evidence_ids": ["metric:orders-db:cpu:18"]
    },
    {
      "service": "checkout-api",
      "reason": "A concurrent latency spike could have an independent origin",
      "supporting_evidence_ids": ["metric:checkout-api:p99_latency:21"],
      "contradicting_evidence_ids": []
    }
  ],
  "missing_evidence": ["orders-db connection-pool telemetry prior to first timeout"],
  "next_check": {
    "service": "orders-db",
    "signal": "connection-pool saturation",
    "window": "2 minutes before first timeout",
    "purpose": "Differentiate DB exhaustion from upstream overload",
    "availability": "not present in demo data"
  },
  "limitations": ["No distributed traces supplied"],
  "evidence_provenance_verified": true
}
```

Do not output ungrounded probability percentages or invented evidence identifiers.

---

## 6. Technical architecture

```text
Public benchmark adapter / local synthetic demo
                    |
        Schema + provenance validation
                    |
     Telemetry store (metrics, logs, traces)
                    |
      Incident feature extraction + anomaly signals
                    |
    Root-cause candidate retrieval / ML ranking
                    |
       Service dependency context (optional)
                    |
   Evidence ledger + hypothesis construction
                    |
     EvidenceGap counter-hypothesis checker
                    |
  Uncertainty/abstention + next-check selector
                    |
      API + UI + exportable incident report
                    |
       Reproducible evaluation harness
```

### Suggested stack (use only where justified)

- **Core:** Python 3.11, Pandas, NumPy, scikit-learn, SciPy; Pydantic for strict schemas; NetworkX for graph methods; PyArrow/Parquet for local data; Plotly for charts.
- **ML baselines:** robust statistical change/anomaly ranking; an interpretable supervised ranker/classifier if training support is valid; optional gradient-boosted model. A GNN is **not required** unless it beats a simpler baseline under rigorous comparison.
- **API:** FastAPI with `/health`, `/incidents`, `/incidents/{id}`, `/analyze`, `/evidence/{id}`, `/reports/{id}`; version schemas and validate inputs.
- **UI:** Streamlit for quick cross-platform setup and interactive investigation; keep all inference in importable Python modules or API, not embedded in UI cells.
- **LLM (optional):** provider-agnostic adapter using environment variables, timeouts, bounded context, explicit tool descriptions, JSON schemas, budget constraints, and evidence-ID validation. Default to `LLM_MODE=off`. Never let the model call destructive tools.
- **MLOps/testing:** pytest, ruff, type checking, deterministic seeds, GitHub Actions, Docker/Docker Compose, dependency lockfile, model/data version metadata, MLflow **optional**.
- **Storage:** SQLite for metadata and local report state; Parquet for local telemetry. Avoid Kubernetes or a cloud account as a prerequisite for the demo.

### API/agent safety

Treat log strings as untrusted content that may include malicious prompt instructions. LLM tools must allow only bounded, read-only access to allowlisted incident data. Validate every reported evidence ID against actual records and reject/flag unsupported citations. Do not permit code execution, shell commands, autonomous config changes, or silent data exfiltration by the investigator. Keep report generation deterministic where practical.

---

## 7. Scientific methodology and evaluation

**Baseline progression:**

1. Chance/naive ranker and simple rule-based signatures.
2. Statistical metric anomaly/change detection and symptom-to-service aggregation.
3. A learned ranker/classifier where the dataset supports training and disjoint testing.
4. Graph-augmented candidate scoring, when actual topology exists.
5. LLM-only investigation on the **same evidence budget** as an optional comparison.
6. **EvidenceGap hybrid** and component-wise ablations.

**Do not train on test incident labels.** Fit normalization, thresholds, calibrators, feature selection and retrieval parameters only on training/validation splits. Preserve a frozen test set. Evaluate repeated runs with seeds, uncertainty intervals where meaningful, per-system breakdowns, and visible failure analyses.

**Mandatory report table columns:** model/configuration; evaluated dataset and split; Top-1; Top-3; coverage; answered-case accuracy; evidence-citation validity; unsupported-claim rate; latency; API cost if applicable. Use `N/A` rather than making up values that cannot be measured.

**Originality verification:** Before implementation, create `docs/RELATED_WORK.md` describing how CausaTrace differs from RCAEval baselines, OpenRCA/RCA-Agent, and other evidence-grounding / abstaining RCA approaches. Cite sources and state overlap. A distinctive engineering implementation is achievable; a new scientific contribution is an **empirical question**.

**No invented evaluation:** Never commit fake benchmark results, fabricated performance improvements, unexecuted test badges, placeholder screenshots presented as real, or unverified claims of production readiness.

---

## 8. GitHub-first delivery: required from the beginning

I use GitHub to track the code, documentation, and milestone history.

1. Propose the repository name **`causatrace`** (check availability). Prepare its description and topics: `aiops`, `root-cause-analysis`, `machine-learning`, `explainable-ai`, `observability`, `mlops`, `fastapi`.
2. Initialize local `git`, `.gitignore`, `README.md`, `LICENSE` (select an appropriate license with owner approval), `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (optional), `pyproject.toml`, tests, `.env.example`, GitHub workflow, and this project specification. **Never publish secrets.**
3. Create the remote repository through GitHub CLI (`gh`) or a supported GitHub integration **only when the owner has authenticated and explicitly authorized creation**. If authentication is missing, leave a complete local repository and provide exact `gh auth login`, `gh repo create ...`, and `git push` steps. Do not claim a remote exists without verifying its URL.
4. Make focused commits with meaningful history for each completed milestone. Use issues/milestones or `docs/ROADMAP.md` and maintain a changelog as work progresses.
5. All key workflows must work from a clean checkout, including setup, sample demo, tests, and benchmark download instructions.
6. Only call the project complete after running the documented commands in a clean environment and inspecting their output. Configure CI to execute the offline smoke tests and prevent regressions.
7. Ensure all assets have clear licenses and attribution. Avoid pushing source datasets unless redistribution terms allow it; do not ship proprietary material.
8. Add a polished project landing README with the mission, problem, architecture, *real* screenshots/demo GIF when available, feature tour, quickstart, dataset instructions, methodology, known limitations, references, and roadmap. Pin the repository on the owner’s GitHub profile once published (owner-controlled step).

### Desired repository structure

```text
causatrace/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── .github/workflows/ci.yml
├── pyproject.toml
├── uv.lock                       # or equivalent pinned lockfile
├── Dockerfile
├── compose.yaml
├── docs/
│   ├── PROJECT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DATASETS.md
│   ├── RELATED_WORK.md
│   ├── EVALUATION.md
│   ├── REPRODUCIBILITY.md
│   └── ROADMAP.md
├── data/
│   ├── demo/                     # tiny, self-authored public fixtures
│   └── raw/                      # gitignored downloads
├── configs/
├── src/causatrace/
│   ├── schemas/
│   ├── datasets/
│   ├── features/
│   ├── baselines/
│   ├── ranking/
│   ├── graph/
│   ├── evidence/
│   ├── verification/             # EvidenceGap
│   ├── agents/                   # optional LLM mode
│   ├── evaluation/
│   ├── api/
│   └── reporting/
├── app/                           # Streamlit
├── scripts/
│   ├── download_data.py
│   ├── run_demo.py
│   ├── evaluate.py
│   └── validate_install.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── reports/                       # generated files gitignored
```

### Minimum friction / installation contract

The README must support **Windows 11 + PowerShell**, Linux/macOS shell, and Docker. Make the application runnable without a GPU, cloud account, or LLM credentials.

**Proposed user flows**

```bash
# Python path — commands must be verified before publishing
 git clone <VERIFIED_REPO_URL>
 cd causatrace
 python -m venv .venv
 # activate environment as documented for the OS
 pip install -e '.[dev]'
 python scripts/validate_install.py
 python scripts/run_demo.py
 pytest -q
 streamlit run app/Home.py
```

```bash
# Docker path — verify before publishing
 docker compose up --build
```

A benchmark download is a **separate opt-in command** with expected size/destination; a model/API key is **never** required to run the included demo. On first run the app should display at least two demo incidents: one with sufficient evidence for a proposed cause, and one purposely ambiguous case where abstention is appropriate. These fixtures must be described as synthetic and illustrative.

---

## 9. Implementation milestones

### M0 — Repository and feasibility gate

- Inspect official datasets, check licensing, try a tiny fetch/sample, verify file schemas, and document assumptions.
- Initialize Git repo and baseline structure; create remote **only with user authorization**.
- Build the offline fixture, smoke-test, README and CI skeleton.
- **Acceptance:** clean checkout + offline sample runs; zero secrets committed; sources documented.

### M1 — Data adapters and exploratory analysis

- Parse RCAEval selected subsets and preserve source/ground truth metadata separately.
- Validate data schema, missing modalities and timestamp alignment; add quality reports.
- **Acceptance:** fixed incidents load reproducibly; corrupt/missing data yields clear errors.

### M2 — Meaningful ML baselines

- Implement naive, rules/statistical, and if justified, learned rankings.
- Prevent leakage; save experiment configs and metrics; test against benchmark annotation.
- **Acceptance:** documented, repeatable baseline evaluation with honest results.

### M3 — EvidenceGap research feature

- Evidence ledger; hypothesis comparison; contradiction checks; next-evidence suggestion; abstention policy; deterministic fallback.
- Benchmark ablations against M2 and a small annotated evidence-fidelity subset.
- **Acceptance:** citations are resolvable; an ambiguous incident reliably triggers appropriate uncertainty; evaluation captures successes **and failures**.

### M4 — User-facing application

- API + telemetry explorer + EvidenceGap view + exportable reports.
- Add robust validation, helpful errors and tests; Docker Compose.
- **Acceptance:** someone unfamiliar with the project can diagnose a demo case by following the README.

### M5 — Optional LLM mode + hardening

- Add safe read-only, schema-constrained investigator if it genuinely improves outcomes.
- Test prompt injection in logs, token budgets, provider outages, timeouts and unsupported outputs.
- **Acceptance:** fully functional offline mode survives LLM outages; no destructive capability.

### M6 — Portfolio release and reproducibility audit

- Create real screenshots, 60–120-second demo, architecture diagram, evaluation chart/table, examples and limitations.
- Run quickstart from a clean install and verify CI; check links, attribution and repo remote.
- **Acceptance:** versioned release, public documentation, evidence-backed claims and reproducible run instructions.

**Prioritization:** M0–M4 before polishing advanced agents. A robust small system with evaluated ML is better than a complex but untested multi-agent demo.

---

## 10. Definition of done

The project is **not complete** until every item below is met:

- [ ] A GitHub repository has been created by an authorized owner, or exact pending authentication instructions are recorded; the actual remote URL is verified.
- [ ] Public README, architecture, dataset licenses/attribution, setup guide and limitations are complete.
- [ ] Clean Windows, Linux/macOS, and Docker setup paths are documented; at least one clean OS installation and Docker run have been actually executed and logged (other paths tested where environments are available).
- [ ] Offline sample demo works without API key, GPU, or benchmark download.
- [ ] At least one genuine public benchmark is downloaded via an explicit script and evaluated with leakage-safe splits.
- [ ] At least two meaningful baselines plus EvidenceGap are compared; ablations exist; numbers are not invented.
- [ ] Dashboard, API, evidence provenance, hypothesis comparison, abstention, next check, JSON/Markdown report work end-to-end.
- [ ] Tests pass in CI and local environment; malformed input, missing modality, API outage, and adversarial log text are handled safely.
- [ ] No proprietary information, credentials, unlicensed dataset copies, or excessively large artifacts are tracked by Git.
- [ ] Real demo video and screenshots are captured from working software; reproducibility instructions are verified.

---

## 11. Development notes

I review the tests and open questions at the end of each milestone. The [roadmap](ROADMAP.md) tracks what I plan to build next, and the [reproducibility notes](REPRODUCIBILITY.md) record what I have run.

---

## 12. Research references and provenance

These are **sources to inspect and cite in the repo**, not evidence that our implementation already exists or is novel:

1. RCAEval authors' GitHub repository: https://github.com/phamquiluan/RCAEval
2. RCAEval Hugging Face dataset: https://huggingface.co/datasets/phamquiluan/RCAEval
3. RCAEval archived dataset DOI: https://doi.org/10.5281/zenodo.14590730
4. OpenStack-RCA-Bench research description: https://conf.researchr.org/details/ase-2026/ase-2026-tools-and-data-sets/58/OpenStack-RCA-Bench-A-Reproducible-IaaS-Root-Cause-Analysis-Dataset
5. OpenStack-RCA-Bench data archive: https://zenodo.org/records/20136820
6. Microsoft OpenRCA benchmark and repository: https://microsoft.github.io/OpenRCA/ and https://github.com/microsoft/OpenRCA

**Final note:** A unique brand name and more features do not prove a unique scientific method. CausaTrace's differentiation must be earned through transparent implementation, a verified evidence ledger, carefully designed uncertainty handling, comparative experiments and usable end-to-end software.
