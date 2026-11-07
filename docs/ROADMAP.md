# CausaTrace roadmap

I want this project to answer two questions. Can a model learn to rank the service that caused an incident? When the evidence is mixed, can CausaTrace pick a check that helps narrow down the cause? I'll build and test those pieces before putting them behind a dashboard.

## What I've done so far

I put the project on GitHub, ran both synthetic cases from a fresh Windows clone, and saw the smoke tests pass on Windows and Linux in GitHub Actions. I checked the format and coverage of small RCAEval samples. The [dataset notes](DATASETS.md) record which files I checked and what still needs to be verified. I evaluated the rankers on Online Boutique and Sock Shop, added a Train Ticket investigation with all three telemetry sources, and reviewed the related work. [Evaluation](EVALUATION.md) · [Related work](RELATED_WORK.md)

## Milestones and release status

| Milestone | What I'll build and how I'll check it |
| --- | --- |
| M1 — Load real incidents | Start with RCAEval metrics, then add logs and traces where the data supports them. Pin the source revision, keep source IDs, check timestamps, and record missing data. Keep fault labels and fault-coded paths separate from model inputs. Verify that the same cases load consistently and bad inputs get clear errors. |
| M2 — Train a service ranker | Train a supervised model on real cases and compare it with a simple rule and a statistical anomaly baseline. Give all three the same inputs and candidates. Report Top-1, Top-3, and mean reciprocal rank on a frozen test split, with examples of where each method fails. |
| M3 — Build EvidenceGap | Compare plausible causes, link claims to observations, and show contradictory or missing evidence. Test when the system should hold off on a diagnosis and whether its next check improves the investigation. |
| M4 — Build the app | Run a full investigation in the dashboard and through the documented API. Inspect telemetry, compare causes, follow evidence links, and export JSON and Markdown reports. Test malformed inputs and missing telemetry. |
| M5 — Try an LLM if it helps | Keep the offline workflow working on its own. If I add an LLM, compare it at the same evidence budget and test read-only access, misleading log text, invalid citations, and outages. |
| M6 — Prepare the release | Follow the setup and experiment instructions from a fresh clone. Pin dependencies, verify the local or Docker workflow and CI, check attribution, and record a demo of the working app. |

## How I'll test it

For ranking, I'll start with a logistic model using features such as anomaly size, when the change starts, and how long it lasts. I'll try a more flexible model if the validation results justify it. I'll keep repeated injections together, check for shared captures or overlapping scenarios across splits, and fit preprocessing and thresholds on development data. I'll test a held-out system separately to see how well the model transfers. If I use injection time as a proxy for the time an alert arrives, I'll say so and check how sensitive the results are to shifting it.

For EvidenceGap, I'll check two things separately. Can I open the record a claim cites, and does that record actually support the claim? I'll review a small set of examples using written criteria. I'll report accuracy at different levels of coverage so it's clear what happens when the system answers fewer cases. I'll assess probability calibration if there are enough held-out cases.

For Active Evidence Acquisition, I'll replay recorded incidents. Each policy starts with the same visible data and can reveal a signal for a service and time window. I'll estimate which check is expected to reduce uncertainty about the cause the most for its cost, using an outcome model fitted on training incidents. The score will account for possible causes beyond the leading pair. I'll compare that policy with fixed-order, highest-anomaly, and seeded random checks, plus a run with no checks. I'll measure accuracy and coverage at the same budget, the number of checks, the data revealed, and latency. I'll report uncertainty intervals where the sample supports them.

A replay can reveal data that was recorded and deliberately held back. If a signal was never collected, I'll show that it is unavailable. I'll also run the evaluation with contradiction checks, acquisition, and abstention removed in turn to see which parts actually help.

The first preview covers the offline dashboard, the pinned RCAEval
experiments, the citation and abstention audit, and the Train Ticket
walkthrough. The benchmark replay measures acquisition separately from
the dashboard. I kept the offline workflow deterministic and left the
LLM milestone optional.

The portfolio release adds a recorded walkthrough, real screenshots,
an automated review of 641 metric claims, and a contradiction
experiment at equal coverage. I documented the cases where a simpler
policy did better. The multimodal review covers one Train Ticket
incident, and the ranking results cover the two recorded systems in
the evaluation.
