# CausaTrace

I'm building CausaTrace to help investigate failures in distributed systems. When several services start throwing errors at once, I want to see which service is the most likely starting point, what evidence points to it, and what I should check next if two explanations still fit.

Right now, the offline demo loads two synthetic incidents and prints their observations with evidence IDs. I also checked samples from RCAEval for the benchmark work. The next step is to load real metrics in a repeatable way and keep the fault labels separate from what the model sees.

[Roadmap](docs/ROADMAP.md) · [Dataset notes](docs/DATASETS.md) · [Project design](docs/PROJECT_SPEC.md)

## Run the offline demo on Windows

From the project folder, open PowerShell and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe .\scripts\run_demo.py
.\.venv\Scripts\python.exe .\scripts\run_demo.py demo-002
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The demo prints observations and their evidence IDs for two included synthetic incidents. It runs offline using Python's standard library. The smoke tests verify that both incidents load and print the expected IDs.
