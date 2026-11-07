# Reproducibility

I checked the offline quickstart from a fresh Windows clone with Python 3.12. Both included incidents loaded before I installed the benchmark packages. I then installed the pinned dependencies, downloaded the Train Ticket files, and built the report in that clone. [Quickstart](../README.md#run-it-locally) · [Train Ticket commands](DATASETS.md#investigate-train-ticket-with-three-sources)

For the full local suite, run these commands in PowerShell from the project folder after creating the virtual environment. On Linux or macOS, use `.venv/bin/python`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-benchmark.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

All 17 tests passed for the current dashboard. GitHub Actions runs the suite on Windows and Linux. The Docker job builds and starts the offline dashboard, waits for it to respond, and checks the page plus the JSON and Markdown exports. I published the versioned release manually after CI passed. [Workflow](../.github/workflows/ci.yml) · [Dashboard checks](https://github.com/Nancy2820047/causatrace/pull/11/checks)

For the dashboard refresh, I checked all three incident views in Edge, followed evidence links, tested both report downloads, and checked the layout at 390 and 320 pixels wide. The walkthrough was recorded from the running v0.1.0 app. [Current dashboard screenshot](media/train-ticket.png) · [Release walkthrough](https://github.com/Nancy2820047/causatrace/releases/tag/v0.1.0)
