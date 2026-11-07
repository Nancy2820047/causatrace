# How the offline investigation works

I kept the first dashboard small so I could check the whole flow with
the two included incidents. The browser asks a local HTTP server for
the incident report. The server loads the fixture and runs the timing
check in scripts/evidence_gap.py. The report lists candidate services,
the records behind their claims, and a next check when timing leaves
the two leading candidates tied.

| Request | Response |
| --- | --- |
| GET / | Incident dashboard |
| GET /api/incidents | Included incident IDs |
| GET /api/incidents/demo-001 | JSON report with source observations |
| GET /api/incidents/demo-001.md | Markdown report with evidence IDs |
| GET /api/incidents/demo-002 | JSON report that asks for more evidence |

The server binds to 127.0.0.1. An unknown incident returns a JSON 404.
Every citation resolves against the observations in that incident.
A timestamp tie triggers an abstention and reports whether the proposed
signal exists in the requested time window. An earlier symptom gives
the investigator a lead. Establishing a cause would need more evidence.

The dashboard currently uses synthetic fixtures and a timing rule.
The learned ranker and acquisition policies run in the separate
benchmark experiments. Bringing real incidents into the dashboard and
evaluating whether claims are grounded are still open.
