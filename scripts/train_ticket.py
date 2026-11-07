"""Inspect one pinned Train Ticket incident across all three sources."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from scripts.evaluate_rcaeval import extract_features
from scripts.inspect_rcaeval import CACHE, FILES, REVISION, download_sample, load_label, load_metrics, verify

CASE = "re2tt_ts-order-service_cpu_1"
INCIDENT = "train-ticket"
ASSETS = {
    "cases.parquet": FILES["cases.parquet"],
    f"{CASE}/metrics.parquet": (1023946, "98b3bca0944f8b9d505d07078f55723e6e9f29e2186a4dcc7a2e807d9b000645"),
    f"{CASE}/logs.parquet": (2921420, "d1bfbc44853434a97ac16f57cc83ef46297262b51fe0c0e28e4ca90494245c88"),
    f"{CASE}/traces.parquet": (15927967, "bb2fe8cf69ff16e8d80f1ef02d20657c55ba23cea8fca2ef1c57476b9b14a18a"),
}


def utc(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def load_report(cache: Path = CACHE) -> dict:
    for path in ASSETS:
        verify((cache / path).read_bytes(), path, ASSETS)
    folder = cache / CASE
    alert = load_label(cache / "cases.parquet", CASE).injection_time
    end = alert + 120
    services, values, metrics = extract_features(load_metrics(folder / "metrics.parquet"), alert)
    candidates = [services[index] for index in np.argsort(-values[:, 0], kind="stable")[:3]]
    logs = pq.read_table(folder / "logs.parquet", columns=["timestamp", "container_name"])
    spans = pq.read_table(folder / "traces.parquet", columns=[
        "startTimeMillis", "traceID", "spanID", "parentSpanID", "serviceName",
    ])
    log_times = logs["timestamp"].to_numpy()
    span_times = spans["startTimeMillis"].to_numpy()
    indices = np.flatnonzero((span_times >= alert * 1000) & (span_times < end * 1000))
    span_rows = [
        (int(index), row)
        for index, row in zip(
            indices,
            spans.take(indices).to_pylist(),
        )
    ]
    parents = {(row["traceID"], row["spanID"]): row for _, row in span_rows}
    observations = []
    hypotheses = []
    log_services = np.array(logs["container_name"].to_pylist())
    for service in candidates:
        metric = metrics[service].copy()
        metric.update(timestamp=utc(metric["timestamp"]), file="metrics.parquet")
        observations.append(metric)
        evidence = [{
            "observation_id": metric["id"], "relation": "supporting",
            "reason": "This metric deviated from its pre-alert baseline.",
        }]
        matches = np.flatnonzero((log_times >= alert) & (log_times < end) & (log_services == service))
        if matches.size:
            index = int(matches[0])
            observations.append({
                "id": f"log:{index}", "row_index": index, "file": "logs.parquet",
                "service": service, "signal": "log record", "value": service,
                "timestamp": utc(int(log_times[index])),
            })
            evidence.append({
                "observation_id": f"log:{index}", "relation": "ambiguous",
                "reason": f"{len(matches)} log records name this service in the window. Presence alone does not indicate an error.",
            })

        for index, span in span_rows:
            if span["serviceName"] != service:
                continue
            parent = parents.get((span["traceID"], span["parentSpanID"]))
            if parent is None or parent["serviceName"] == service:
                continue
            observations.append({
                "id": f"span:{index}", "row_index": index, "file": "traces.parquet",
                "service": service, "signal": "parent service", "value": parent["serviceName"],
                "timestamp": utc(span["startTimeMillis"] / 1000),
                "trace_id": span["traceID"], "span_id": span["spanID"],
                "parent_span_id": span["parentSpanID"],
            })
            evidence.append({
                "observation_id": f"span:{index}", "relation": "ambiguous",
                "reason": "A parent span in the same trace connects these services. The link does not locate the fault.",
            })
            break
        hypotheses.append({"service": service, "evidence": evidence})
    return {
        "incident_id": INCIDENT, "synthetic": False, "status": "NEEDS_INVESTIGATION",
        "reason": "Metric anomalies suggest leads. Logs and trace links provide context for checking them.",
        "source": {"dataset": "RCAEval RE2 Train Ticket", "case": CASE, "file": "metrics, logs and traces", "revision": REVISION},
        "observations": observations, "hypotheses": hypotheses, "next_check": None,
        "limitations": [
            "The recorded injection time is a proxy alert. Each source uses the same two-minute post-alert window.",
            "Candidates are ranked by metric anomaly only. Log records and trace links provide context.",
            "Only parent spans captured in the same window are linked here.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        download_sample(CACHE, ASSETS)
    report = load_report()
    print(report["incident_id"], [row["id"] for row in report["observations"]])
