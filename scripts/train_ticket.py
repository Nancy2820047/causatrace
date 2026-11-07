"""Inspect one pinned Train Ticket incident across all three sources."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

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


def compare_call_path(span_rows, parents, span, parent, alert_ms: int) -> tuple[str, dict]:
    """Compare spans on the cited edge and operation in the two sampled windows."""
    before = []
    after = []
    for _, row in span_rows:
        if (row["serviceName"], row["operationName"]) != (span["serviceName"], span["operationName"]):
            continue
        caller = parents.get((row["traceID"], row["parentSpanID"]))
        if caller is None or caller["serviceName"] != parent["serviceName"]:
            continue
        window = before if row["startTimeMillis"] < alert_ms else after
        window.append(row)

    summaries = []
    comparison = {}
    for label, window in (("before", before), ("after", after)):
        durations = [row["duration"] for row in window if row["duration"] is not None]
        recorded = sum(row["statusCode"] is not None for row in window)
        duration = median(durations) if durations else None
        comparison[label] = {"median": duration, "spans": len(window)}
        timing = f"median raw duration {duration:g}" if duration is not None else "duration unavailable"
        summaries.append(f"{len(window)} spans {label} the alert, {timing}, {recorded} with status codes")
    return (
        f"Matched {parent['serviceName']} to {span['serviceName']} on {span['operationName']}. "
        + ". ".join(summaries)
        + ". The comparison describes this call path and leaves the origin uncertain.",
        comparison,
    )



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
        "operationName", "duration", "statusCode",
    ])
    log_times = logs["timestamp"].to_numpy()
    span_times = spans["startTimeMillis"].to_numpy()
    indices = np.flatnonzero((span_times >= (alert - 120) * 1000) & (span_times < end * 1000))
    span_rows = [
        (int(index), row)
        for index, row in zip(
            indices,
            spans.take(indices).to_pylist(),
        )
    ]
    parents = {(row["traceID"], row["spanID"]): row for _, row in span_rows}
    scores = {service: float(score) for service, score in zip(services, values[:, 0])}
    tied_leads = scores[candidates[0]] == scores[candidates[1]]
    observations = []
    hypotheses = []
    log_services = np.array(logs["container_name"].to_pylist())
    for service in candidates:
        metric = metrics[service].copy()
        metric.update(timestamp=utc(metric["timestamp"]), file="metrics.parquet")
        observations.append(metric)
        evidence = [{
            "observation_id": metric["id"], "relation": "supporting",
            "reason": (
                f"The cited sample was {metric['value']:.4g}, compared with a pre-alert median "
                f"of {metric['baseline_median']:.4g}. The service anomaly score was "
                f"{scores[service]:.2f} on a scale capped at 100."
            ),
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
            if span["serviceName"] != service or span["startTimeMillis"] < alert * 1000:
                continue
            parent = parents.get((span["traceID"], span["parentSpanID"]))
            if parent is None or parent["serviceName"] == service:
                continue
            reason, comparison = compare_call_path(span_rows, parents, span, parent, alert * 1000)
            observations.append({
                "id": f"span:{index}", "row_index": index, "file": "traces.parquet",
                "service": service, "signal": "parent service", "value": parent["serviceName"],
                "timestamp": utc(span["startTimeMillis"] / 1000),
                "trace_id": span["traceID"], "span_id": span["spanID"],
                "parent_span_id": span["parentSpanID"],
                "duration_comparison": comparison,
            })
            evidence.append({
                "observation_id": f"span:{index}", "relation": "ambiguous",
                "reason": reason,
            })
            break
        hypotheses.append({"service": service, "evidence": evidence})
    return {
        "incident_id": INCIDENT, "synthetic": False, "status": "NEEDS_INVESTIGATION",
        "reason": (
            "The leading candidates tie on the capped metric score. Logs and trace links provide context."
            if tied_leads else "Metric anomalies suggest leads. Logs and trace links provide context."
        ),
        "source": {"dataset": "RCAEval RE2 Train Ticket", "case": CASE, "file": "metrics, logs and traces", "revision": REVISION},
        "observations": observations, "hypotheses": hypotheses,
        "next_check": {
            "service": "ts-order-service",
            "signal": "trace span durations by caller and operation",
            "start": utc(alert - 120),
            "end_exclusive": utc(end),
            "purpose": "Check whether the slowdown also appears on calls from the seat and payment services.",
            "availability": "available",
        },
        "limitations": [
            "The recorded injection time is a proxy alert. Metric and log citations use the two minutes after the alert. Trace comparisons include the two minutes before it.",
            "Candidates are ranked by metric anomaly only. Log records and trace links provide context.",
            "Trace comparisons use resolved parent links in the four-minute sample and retain raw duration units.",
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
