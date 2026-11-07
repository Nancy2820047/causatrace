# Related work

[RCAEval](https://github.com/phamquiluan/RCAEval) supplies labeled fault-injection cases and existing statistical and graph RCA baselines. We plan to compare learned localization and EvidenceGap using explicitly documented inputs, splits and scoring. Any benchmark method that receives the true injection time must be compared under the same timing contract.

[OpenRCA and RCA-Agent](https://github.com/microsoft/OpenRCA) already investigate multimodal telemetry through iterative data retrieval and analysis. CausaTrace will test a separate question: whether explicit counter-evidence and a cost-aware choice of the next telemetry slice improve investigation under matched replay budgets.

This is an initial comparison. A broader primary-literature review of selective RCA, evidence grounding and active feature acquisition remains an M0 task. The proposed combination has no verified novelty claim.

## Where my experiments fit

CauseLens uses metrics and traces to build a structural causal model
and uses counterfactual analysis to examine propagation. My current
experiment is narrower. It compares competing leads from recorded
metric anomalies and keeps each observation traceable to its source.
[CauseLens](https://ieeexplore.ieee.org/abstract/document/11143407)

Covert and colleagues studied greedy conditional mutual information
for dynamic feature selection. I use that idea to choose the next
service window in a replay. The question I can test here is whether
that choice helps on RCAEval at the same budget as simpler policies.
[Learning to Maximize Mutual Information for Dynamic Feature Selection](https://proceedings.mlr.press/v202/covert23a.html)

These are points of comparison for the current design. I have not
established research novelty.
