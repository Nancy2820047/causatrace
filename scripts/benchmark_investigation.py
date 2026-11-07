"""Build a dashboard report for the first case in the frozen test set."""

from datetime import datetime, timedelta, timezone

import numpy as np

from scripts.evaluate_rcaeval import CACHE, REVISION, cases_and_splits, extract_features, features
from scripts.evaluate_rcaeval import fit_ranker, load_metrics


BENCHMARK_ID = "benchmark-001"


def train_benchmark_ranker(splits):
    train = []
    for case in splits["train"]:
        if case.time_start < case.inject_time <= case.time_end:
            metrics = load_metrics(CACHE / case.case / "metrics.parquet")
            services, values = features(metrics, case.inject_time)
            train.append((case, services, values))
    return fit_ranker(train)

def load_benchmark_report() -> dict:
    splits = cases_and_splits()
    model = train_benchmark_ranker(splits)
    case = min(splits["test"], key=lambda row: row.case)
    return build_benchmark_report(case, model)


def build_benchmark_report(case, model) -> dict:
    table = load_metrics(CACHE / case.case / "metrics.parquet")
    services, values, evidence = extract_features(table, case.inject_time)
    learned = model.decision_function(values)
    statistical = values[:, 0]
    order = list(np.argsort(-learned, kind="stable"))
    statistical_lead = int(np.argmax(statistical))
    candidates = order[:3]
    if statistical_lead not in candidates:
        candidates.append(statistical_lead)

    observations = []
    hypotheses = []
    for index in candidates:
        service = services[index]
        item = evidence[service].copy()
        item["timestamp"] = datetime.fromtimestamp(item["timestamp"], timezone.utc).isoformat()
        observations.append(item)
        citations = [{
            "observation_id": item["id"],
            "relation": "supporting",
            "reason": (
                f"This is the peak sampled value by absolute deviation for {item['signal']}. "
                f"The pre-alert median was {item['baseline_median']:.4g}."
            ),
        }]
        if statistical_lead != index and statistical[statistical_lead] > statistical[index]:
            citations.append({
                "observation_id": evidence[services[statistical_lead]]["id"],
                "relation": "contradicting",
                "reason": "A competing service has a stronger robust anomaly score.",
            })
        hypotheses.append({"service": service, "evidence": citations})

    lead = services[order[0]]
    agree = order[0] == statistical_lead
    alert = datetime.fromtimestamp(case.inject_time, timezone.utc)
    return {
        "incident_id": BENCHMARK_ID,
        "synthetic": False,
        "source": {"dataset": "RCAEval RE1-OB", "revision": REVISION,
                   "case": case.case, "file": "metrics.parquet"},
        "observations": observations,
        "hypotheses": hypotheses,
        "ranking": {
            "learned_lead": lead,
            "statistical_lead": services[statistical_lead],
            "learned_margin": float(learned[order[0]] - learned[order[1]]) if len(order) > 1 else 0.0,
        },
        "status": "NEEDS_INVESTIGATION",
        "reason": (
            "Both rankers favor the same service. Metrics alone leave the origin uncertain."
            if agree else "The learned ranker and the anomaly baseline favor different services."
        ),
        "next_check": {
            "service": lead,
            "signal": "upstream and downstream request spans",
            "start": (alert - timedelta(seconds=120)).isoformat(),
            "end_exclusive": (alert + timedelta(seconds=120)).isoformat(),
            "purpose": "Check whether the candidate's request errors precede failures in related services.",
            "availability": "missing",
        },
        "limitations": [
            "The recorded injection time is a proxy for the alert.",
            "RE1 has metrics only. The next check would require separate trace data.",
            "Anomaly evidence suggests leads. The ranker scores are uncalibrated.",
        ],
    }
