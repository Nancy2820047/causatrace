# CausaTrace

CausaTrace investigates distributed-system incidents by ranking suspect services, linking explanations to telemetry, and identifying the next check that could distinguish competing causes.

Development starts with the [M0 feasibility checkpoint](docs/ROADMAP.md). See the [dataset notes](docs/DATASETS.md) and [original project specification](docs/PROJECT_SPEC.md).

## Run the offline demo on Windows

From the project folder, open PowerShell and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe .\scripts\run_demo.py
.\.venv\Scripts\python.exe .\scripts\run_demo.py demo-002
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The demo prints observations and their evidence IDs for two included synthetic incidents. It runs offline using Python's standard library. The smoke tests verify that both incidents load and print the expected IDs.
