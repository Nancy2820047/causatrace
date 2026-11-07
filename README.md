# CausaTrace

I'm building CausaTrace to help investigate failures in distributed systems. When several services start throwing errors at once, I want to see which service is the most likely starting point, what evidence points to it, and what I should check next if two explanations still fit.

Right now, the offline demo loads two synthetic incidents and prints their observations with evidence IDs. I also checked samples from RCAEval for the benchmark work. I ran the first ranking experiment on Online Boutique. The statistical baseline led on this split, and I recorded the setup and failure cases so I can compare future changes against it.

[Roadmap](docs/ROADMAP.md) · [Dataset notes](docs/DATASETS.md) · [Project design](docs/PROJECT_SPEC.md) · [First benchmark results](docs/EVALUATION.md)

## Run the offline demo on Windows

From the project folder, open PowerShell and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe .\scripts\run_demo.py
.\.venv\Scripts\python.exe .\scripts\run_demo.py demo-002
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_demo.py -v
```

The demo prints observations and their evidence IDs for two included synthetic incidents. It runs offline using Python's standard library. The smoke tests verify that both incidents load and print the expected IDs.
