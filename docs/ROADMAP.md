# Development roadmap

This roadmap incorporates the owner’s additional requirements and governs implementation alongside the original specification. Review the acceptance criteria and actual results together before advancing. Record failures and unresolved decisions at each checkpoint.

| Milestone | Acceptance criteria |
| --- | --- |
| M0 — Feasibility and foundation | Inspect Git and remotes. Verify a bounded real telemetry sample, labels, terms and known modality limitations. Document related work. Run the two labeled synthetic smoke cases offline in a clean checkout and configure CI. |
| M1 — Benchmark adapters | Load selected pinned cases reproducibly. Preserve provenance, align timestamps and record missingness. Keep labels, fault-coded paths and experiment metadata separate from inference. Audit the split manifest and document input timing assumptions. |
| M2 — Learned ranking | Train at least one supervised service ranker on real cases. Compare with a rule baseline and a robust statistical anomaly baseline on identical candidates and inputs. Reproduce Top-1, Top-3 and MRR on frozen grouped splits and report failures by system and fault. |
| M3 — EvidenceGap | Resolve evidence IDs, test supporting and contradictory observations, record missing signals, and abstain using validation-set thresholds. Compare acquisition policies at matched budgets on held-out replay cases. Report grounding, selective reliability, investigation cost, ablations and failures. |
| M4 — Application | Exercise the dashboard and documented backend API end to end, including telemetry inspection, competing hypotheses, evidence links, next check, abstention and JSON/Markdown export. Validate malformed inputs and missing modalities. |
| M5 — Optional LLM | Include only if a matched-budget evaluation shows a measurable benefit. Test bounded read-only access, prompt injection, invalid citations and outages. Verify offline operation independently. |
| M6 — Release | Reproduce setup, demo and experiment outputs from a fresh clone using pinned dependencies and documented local or Docker workflows. Verify CI, license and attribution, and capture a real investigation demo. Publish only with owner authorization. |

## Proposed experimental design

Start with a shared service-level logistic scoring model using anomaly magnitude, onset order and persistence. Test a small nonlinear ranker if grouped validation supports it. Fit transforms and tune models on development groups only. Group repetitions by system, affected service and fault, audit shared scenario or capture overlap, and use held-out systems as a separate transfer experiment. Candidate services come from available telemetry. Ground truth determines evaluation outcomes, while alert time inputs are declared explicitly and tested for sensitivity to timing shifts.

EvidenceGap compares at least two plausible candidates where available. Each evidence record links to retrievable source observations and carries a support, contradiction, ambiguity or missingness classification with a reason. Measure reference resolution separately from claim support using a reviewed subset and published annotation rules. Report coverage and risk–coverage curves. Assess probability calibration only if held-out sample size supports it.

For Active Evidence Acquisition, replay incidents with an initial visible slice and a fixed menu of checks by service, signal and time window. Withhold the values of candidate checks from features, scores and policy state until selected. Fit a conditional outcome model on training incidents and estimate expected reduction in hypothesis entropy per declared cost, retaining probability mass outside the leading candidates. Compare with fixed-order, highest-current-anomaly and seeded random policies, plus a zero-check reference. Give policies identical initial evidence, available checks, costs and budgets. Report accuracy and coverage by cost, number of checks to decision, bytes or rows revealed, latency and paired uncertainty intervals where supported. Explicitly separate naturally missing signals from intentionally withheld records. Treat replay as retrospective and report unsupported checks as unavailable. Test whether any gain survives removing contradiction checks, acquisition, and abstention.

Compare with related work before claiming a scientific contribution. Keep the offline core independent of LLM services and defer the final data schema, model family and storage choices until feasibility is reviewed.
