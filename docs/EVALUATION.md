# My first RCAEval ranking experiment

I used the 125 Online Boutique cases from RE1 to see whether a learned
ranker could improve on a simple anomaly score. I split by injected
service and fault, keeping all repetitions together. The runner also
checks capture windows for overlap and metric files for duplicates.

I used the recorded injection time as a stand-in for an alert and gave
each method two minutes of metrics on either side. The model sees
telemetry features and that timing input. The fault name, case path and
target service stay in the experiment runner. I excluded two cases
whose injection timestamps fall outside their captures. That left 74
training cases, 24 validation cases and 25 test cases.

| Method | Test Top-1 | Test Top-3 | Test MRR |
| --- | ---: | ---: | ---: |
| First threshold crossing | 16% | 44% | 0.382 |
| Robust anomaly magnitude | 88% | 100% | 0.933 |
| Logistic ranker | 80% | 100% | 0.893 |

The learned model got two fewer cases right overall. It moved the
injected service from second to first on one disk case, but on two
packet-loss cases it put checkout first when adservice was the target.
Both methods got all five CPU cases and all five memory cases right.
The test covers just five service/fault groups, so these numbers are
specific to this split and alert timing. I still need to check other
systems and later alert times.

## Reproduce the experiment

With Python 3.12 and the project environment ready, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-benchmark.txt
.\.venv\Scripts\python.exe -m scripts.evaluate_rcaeval --download
```

The download caches the pinned case index and 125 metric files under
data/raw. Each metric request is capped at 4 MB. The runner writes
reports/re1-ob.json with the split manifest, exclusions, file hashes,
and predictions for each evaluated case. I ran it twice and got the
same report hash. The two synthetic smoke tests still run independently.

## Check whether the ranker transfers to Sock Shop

I evaluated the unchanged Online Boutique model on all 125 RE1 Sock
Shop incidents. I kept the same proxy alert, features, and ranking
methods. The Sock Shop cases stayed out of training and validation.

| Method | Sock Shop Top-1 | Top-3 | MRR |
| --- | ---: | ---: | ---: |
| First threshold crossing | 6.4% | 17.6% | 0.248 |
| Robust anomaly magnitude | 64.8% | 97.6% | 0.801 |
| Logistic ranker | 80.8% | 100% | 0.891 |

The learned ranker placed the injected service first in 101 of 125
cases, compared with 81 for the anomaly baseline. It still trailed the
baseline on the original Online Boutique test split. The transfer test
covers one extra benchmark system and uses the known injection time as
an alert proxy.

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_rcaeval --transfer --download --output reports/re1-transfer.json
```

## Check a one-minute alert delay

I kept the training data and fit fixed, then shifted the validation
and test alerts 60 seconds later. I recomputed both feature windows
around the delayed alert. This tests one delay on recorded cases.

| Test set | Statistical Top-1 at +60 s | Learned Top-1 at +60 s |
| --- | ---: | ---: |
| Online Boutique | 72.0% | 80.0% |
| Sock Shop | 63.2% | 66.4% |

The learned ranker kept its Online Boutique accuracy. Its Sock Shop
accuracy fell from 80.8% to 66.4%, so the transfer gain depends on
when the alert arrives.

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_rcaeval --transfer --alert-offset 60 --output reports/re1-transfer-delay60.json
```
