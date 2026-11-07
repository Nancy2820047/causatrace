# CausaTrace project scope

I built CausaTrace for investigating incidents in systems with several services. I wanted a report that shows why a service is worth checking, where the observation came from, and what to look at next when the cause is uncertain.

## What the project includes

- An offline dashboard with two synthetic incidents and optional RCAEval views for Online Boutique and Train Ticket.
- A report with competing hypotheses, supporting or conflicting evidence, and a next check when the incident has one. Each citation links to an observation, and reports export as JSON or Markdown.
- A ranking experiment with a threshold rule, a statistical anomaly baseline, and a supervised logistic ranker.
- A replay that compares information gain with simpler ways of choosing the next metric window. I also tested when the ranker should withhold an answer and checked the numeric claims attached to its citations.
- Python and Docker quickstarts, automated checks, dashboard screenshots, and a recorded walkthrough.

## How I tested it

I kept repeated injections for the same service and fault together when splitting Online Boutique. Sock Shop was a separate transfer set. I used recorded injection time as a proxy for an alert and tested what happened when I moved the alert a minute later. Labels stay in the evaluation code and are used to score the rankings.

I reviewed the Train Ticket metrics, logs, and traces in the same incident. Its trace evidence shows how one call path changed around the alert. The timing suggests where to look next, and the cause remains open.

The release uses a local Python HTTP server and browser JavaScript. Its benchmark scripts use pinned Python dependencies and download telemetry only when requested. The synthetic fixtures are included in the repository. [Architecture](ARCHITECTURE.md) · [Data and attribution](DATASETS.md) · [Evaluation](EVALUATION.md) · [Evidence replay](EVIDENCE_REPLAY.md)

## Release and research limits

The portfolio release is v0.1.0. The current dashboard includes the later visual refresh on main. The project covers recorded benchmark incidents, with one detailed multimodal example. Broader causal validation and any LLM experiment belong to future research. [Roadmap](ROADMAP.md) · [Reproducibility](REPRODUCIBILITY.md) · [Release](https://github.com/Nancy2820047/causatrace/releases/tag/v0.1.0)
