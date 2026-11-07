# CausaTrace roadmap

I wanted to answer two questions. Can a model rank the service that caused an incident? When the evidence is mixed, can the next check help narrow it down?

| Milestone | Where it landed |
| --- | --- |
| M0 · Feasibility | Checked RCAEval formats and ran two synthetic incidents from a clean Windows clone. |
| M1 · Benchmark data | Pinned the source revision, verified the sample files, and kept fault labels and case paths out of the ranker features. |
| M2 · Service ranking | Compared a rule, an anomaly baseline, and a logistic ranker. Tested transfer to Sock Shop and a one-minute alert delay. |
| M3 · EvidenceGap | Linked claims to observations, checked numeric claims, and measured the tradeoff between accuracy and how many incidents the system answers. Compared acquisition policies in a replay. |
| M4 · Dashboard | Built an incident explorer with competing hypotheses, a timeline, a next check, and JSON and Markdown reports. Added a Train Ticket call duration comparison and a layout that fits phone screens. |
| M5 · Optional LLM | Kept the released workflow offline and deterministic. An LLM would be a separate experiment. |
| M6 · Release | Published v0.1.0 with a recorded walkthrough. Verified the quickstart from a clean Windows clone and ran Windows, Linux, and Docker checks in CI. |

The ranking evaluation covers Online Boutique and Sock Shop. I reviewed metrics, logs, and traces together for one Train Ticket case. The replay evaluates which recorded evidence to reveal next. The dashboard gives a separate next-check recommendation for the incident it shows.

If I extend the research, I'd test more multimodal incidents, use independently reviewed claim labels, and check more alert timings. The current results and their limits are documented with the commands I used. [Dataset notes](DATASETS.md) · [Ranking results](EVALUATION.md) · [Evidence replay and audit](EVIDENCE_REPLAY.md) · [Reproducibility](REPRODUCIBILITY.md)
