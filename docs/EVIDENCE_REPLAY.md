# Can the next metric check help?

I replayed the same Online Boutique incidents with a shorter initial
view. Each policy starts with two minutes before the proxy alert and the
first 30 seconds after it. A check reveals a summary of one service's
metrics from seconds 30 through 119 after the alert. The replay has a
catalog of services with revealable data. It only gives the policy the
outcome of the service it selects.

I used the training cases to estimate how often a check produces a
small, medium or large anomaly for the injected service and for other
services. The information-gain policy uses those distributions and the
current model scores to pick a check. I compared it with checking the
current leader, using a fixed service order, and using a seeded random
order. Each check costs one service window in this experiment.

| Policy | Top-1 before checks | Top-1 after three checks |
| --- | ---: | ---: |
| Information gain | 96% | 96% |
| Current leader | 96% | 96% |
| Fixed order | 96% | 96% |
| Seeded random | 96% | 96% |

All four policies started at 24 of 25 correct and ended there. The
information-gain policy and current-leader policy also had identical
aggregate coverage and answered-case accuracy at every budget. After
three checks, they answered 17 of 25 cases and got 16 of those right.
I set the abstention threshold for each policy and budget using the
validation median score. The scores are for ranking and abstention
experiments. Their probability calibration has yet to be tested.

This run gave me no accuracy gain from extra checks. There was little
room to improve on this split, and the policy uses the same outcome
distributions for every service. The next experiment needs a setting
with more plausible alternatives and different kinds of checks.
This is a retrospective replay of recorded metrics. Evidence citation,
contradiction handling, and an evidence-grounding review are still ahead.

After running the ranking experiment with the download flag, run:

```powershell
.\.venv\Scripts\python.exe -m scripts.replay_rcaeval
```

The runner saves the check sequence and results at each budget in
reports/re1-ob-replay.json.

## Repeat the replay on Sock Shop

I kept the Online Boutique model, outcome distributions, and validation
thresholds and replayed the 125 Sock Shop cases. Every policy started at
80.0% Top-1. After three checks, fixed order reached 84.8%, random stayed
at 80.0%, and both information gain and the current leader reached
79.2%. Fixed order answered 82 of 125 cases and got 78 right at that
budget. Information gain answered 76 and got 72 right.

Checking the current leader and maximizing information gain gave the
same aggregate results again. The current policy has one outcome model
for all checks, so it has little basis for telling them apart. This
experiment gives me a baseline to beat before I use an acquisition
policy to drive recommendations in the app.

After downloading the transfer set using the command in
[EVALUATION.md](EVALUATION.md), run:

```powershell
.\.venv\Scripts\python.exe -m scripts.replay_rcaeval --transfer
```
