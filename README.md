# CausaTrace

I built CausaTrace to make it easier to investigate failures across several services. It shows which services are worth checking, links each claim to its source observation, and suggests a next check when the evidence leaves the cause open.

The dashboard has two synthetic incidents you can try offline. There are also optional RCAEval cases for Online Boutique and Train Ticket. Train Ticket shows metrics, logs, and traces together and compares the same call path before and after the alert.

![CausaTrace dashboard showing an ambiguous incident and its next check](docs/media/ambiguous-incident.png)

## Run it locally

From the project folder, use Python 3.12. On Windows, run these commands in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m scripts.serve_demo
```

On Linux or macOS:

```sh
python3.12 -m venv .venv
.venv/bin/python -m scripts.serve_demo
```

Open the dashboard and choose **demo-001** to follow a leading hypothesis, or **demo-002** to see what happens when both symptoms have the same timestamp. Click a citation to jump to its source, or download the report as JSON or Markdown. Press Ctrl+C in the terminal to stop the server. [Open the local dashboard](http://127.0.0.1:8000)

You can also start the offline dashboard in Docker:

```sh
docker compose up --build
```

Use the same dashboard address. Press Ctrl+C to stop it, then run `docker compose down` to remove the container.

## Try the benchmark cases

Install the pinned benchmark dependencies in the virtual environment first. These commands use PowerShell. On Linux and macOS, use `.venv/bin/python` for the Python commands.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-benchmark.txt
.\.venv\Scripts\python.exe -m scripts.train_ticket --download
.\.venv\Scripts\python.exe -m scripts.serve_demo --train-ticket
```

Select **train-ticket** in the dashboard. For Online Boutique, cache the RE1 cases using the benchmark instructions, then start the server with `--benchmark`. Stop any existing server before starting a different mode on the same port. [Train Ticket walkthrough](docs/DATASETS.md#investigate-train-ticket-with-three-sources) · [Benchmark setup](docs/EVALUATION.md#reproduce-the-experiment)

## What I found

On Online Boutique, the statistical anomaly baseline put the injected service first in 88% of cases, compared with 80% for the learned ranker. On Sock Shop, the same learned ranker reached 80.8%, compared with 64.8% for the statistical baseline. When I moved the alert one minute later, the learned ranker dropped to 66.4% on Sock Shop. [Ranking results](docs/EVALUATION.md)

I also checked 641 numeric claims against their source metrics. In the replay, fixed-order checks did better than information gain on Sock Shop. These results describe the recorded cases and timing assumptions in the experiments. [Evidence audit and replay](docs/EVIDENCE_REPLAY.md)

## Tests and walkthrough

GitHub Actions runs the test suite on Windows and Linux and checks the dashboard and both exports in Docker. I published v0.1.0 on GitHub after the checks passed. The walkthrough shows that release, and the screenshots show the current dashboard. [Reproducibility](docs/REPRODUCIBILITY.md) · [v0.1.0 release and video](https://github.com/Nancy2820047/causatrace/releases/tag/v0.1.0) · [Train Ticket screenshot](docs/media/train-ticket.png)

[Architecture](docs/ARCHITECTURE.md) · [Project scope](docs/PROJECT_SPEC.md) · [Roadmap](docs/ROADMAP.md) · [Related work](docs/RELATED_WORK.md)
