# Related work

[RCAEval](https://github.com/phamquiluan/RCAEval) supplies labeled fault-injection cases and existing statistical and graph RCA baselines. We plan to compare learned localization and EvidenceGap using explicitly documented inputs, splits and scoring. Any benchmark method that receives the true injection time must be compared under the same timing contract.

[OpenRCA and RCA-Agent](https://github.com/microsoft/OpenRCA) already investigate multimodal telemetry through iterative data retrieval and analysis. CausaTrace will test a separate question: whether explicit counter-evidence and a cost-aware choice of the next telemetry slice improve investigation under matched replay budgets.

This is an initial comparison. A broader primary-literature review of selective RCA, evidence grounding and active feature acquisition remains an M0 task. The proposed combination has no verified novelty claim.
