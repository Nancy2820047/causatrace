# Related work

I used RCAEval for the ranking experiments because it provides recorded incidents with labeled injected faults. I kept the same timing inputs across my baselines, since knowing the injection time can affect the comparison. [RCAEval](https://github.com/phamquiluan/RCAEval) · [Ranking results](EVALUATION.md)

OpenRCA and RCA-Agent retrieve and analyze telemetry across several sources. In CausaTrace, I used a fixed set of recorded observations to test whether a chosen check improves service ranking under the same replay budget. [OpenRCA](https://github.com/microsoft/OpenRCA) · [Replay results](EVIDENCE_REPLAY.md)

CauseLens uses metrics and traces to model how faults propagate and applies counterfactual analysis. My dashboard traces each claim back to a recorded observation and leaves the cause open when the evidence is mixed. [CauseLens](https://ieeexplore.ieee.org/abstract/document/11143407)

Covert and colleagues studied greedy conditional mutual information for choosing which features to observe. I used that idea to select service windows in the replay. On Sock Shop, fixed order did better at the same budget. [Learning to Maximize Mutual Information for Dynamic Feature Selection](https://proceedings.mlr.press/v202/covert23a.html) · [Policy comparison](EVIDENCE_REPLAY.md#repeat-the-replay-on-sock-shop)
