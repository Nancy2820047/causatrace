"""Check raw evidence references and compare selective rankings."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pyarrow as pa

from scripts.benchmark_investigation import build_benchmark_report, train_benchmark_ranker
from scripts.evaluate_rcaeval import CACHE, cases_and_splits, load_metrics, load_suite


def verify_ledger(report: dict, table: pa.Table) -> tuple[int, int]:
    observations = {item["id"]: item for item in report["observations"]}
    valid = set()
    for key, item in observations.items():
        signal = item["signal"]
        row = item["row_index"]
        if signal not in table.column_names or not 0 <= row < table.num_rows:
            continue
        timestamp = datetime.fromisoformat(item["timestamp"]).timestamp()
        if (key == f"{signal}:{row}"
                and table[signal][row].as_py() == item["value"]
                and table["time"][row].as_py() == timestamp):
            valid.add(key)

    citations = [
        record["observation_id"]
        for hypothesis in report["hypotheses"]
        for record in hypothesis["evidence"]
    ]
    return sum(reference in valid for reference in citations), len(citations)


def review_claims(report: dict, table: pa.Table, alert: int) -> dict:
    """Recompute what each cited metric can establish from its raw windows."""
    time = table["time"].to_numpy()
    before = (alert - 120 <= time) & (time < alert)
    after = (alert <= time) & (time < alert + 120)
    observations = {item["id"]: item for item in report["observations"]}
    valid = {}
    for key, item in observations.items():
        signal = item["signal"]
        if signal not in table.column_names or signal.partition("_")[0] != item["service"]:
            continue
        values = table[signal].to_numpy()
        baseline = values[before & np.isfinite(values)]
        rows = np.flatnonzero(after & np.isfinite(values))
        if not len(baseline) or not len(rows):
            continue
        center = np.median(baseline)
        scale = max(1.4826 * np.median(np.abs(baseline - center)), abs(center) * 0.01, 1e-9)
        deviations = np.minimum(np.abs(values[rows] - center) / scale, 100)
        peak = rows[np.argmax(deviations)]
        magnitude = np.quantile(deviations, 0.95)
        if (key == f"{signal}:{peak}" and item["row_index"] == peak
                and item["value"] == values[peak]
                and datetime.fromisoformat(item["timestamp"]).timestamp() == time[peak]
                and item["baseline_median"] == center and item["magnitude"] == magnitude):
            valid[key] = magnitude

    counts = Counter()
    for hypothesis in report["hypotheses"]:
        service = hypothesis["service"]
        evidence = hypothesis["evidence"]
        own = next((entry["observation_id"] for entry in evidence if entry["relation"] == "supporting"), None)
        for entry in evidence:
            key = entry["observation_id"]
            relation = entry["relation"]
            passed = key in valid and (
                (relation == "supporting" and observations[key]["service"] == service)
                or (relation == "contradicting" and observations[key]["service"] != service
                    and own in valid and valid[key] > valid[own])
            )
            counts[f"{relation}_reviewed"] += 1
            counts[f"{relation}_passed"] += int(passed)
    return dict(counts)


def contradiction_ablation(rows: list[dict]) -> dict:
    """Keep the same learned predictions and number of answered cases in both arms."""
    checked = [row for row in rows if not row["lead_contradicted"]]
    margin_only = sorted(rows, key=lambda row: (-row["margin"], row["case"]))[:len(checked)]
    return {
        "eligible": len(rows),
        "answered_per_arm": len(checked),
        "correct_with_contradiction_check": sum(row["correct"] for row in checked),
        "correct_with_margin_only": sum(row["correct"] for row in margin_only),
    }


def summarize(rows: list[dict]) -> dict:
    ranked = sorted(rows, key=lambda row: row["margin"], reverse=True)
    agrees = [row for row in rows if row["agree"]]
    accuracy = sum(row["correct"] for row in rows) / len(rows)
    errors = 0
    curve = []
    for index, row in enumerate(ranked, start=1):
        errors += not row["correct"]
        if index == len(ranked) or row["margin"] != ranked[index]["margin"]:
            curve.append({"answered": index, "coverage": index / len(rows), "risk": errors / index})
    return {
        "learned_accuracy": accuracy,
        "agreement_coverage": len(agrees) / len(rows),
        "agreement_answered_accuracy": (
            sum(row["correct"] for row in agrees) / len(agrees) if agrees else None
        ),
        "verified_references": sum(row["valid_citations"] for row in rows),
        "references": sum(row["citations"] for row in rows),
        "risk_coverage": curve,
    }


def run() -> dict:
    splits = cases_and_splits()
    model = train_benchmark_ranker(splits)
    output = {}
    for dataset, cases in (("RE1-OB", splits["test"]), ("RE1-SS", load_suite("RE1-SS"))):
        rows = []
        for case in cases:
            if not case.time_start < case.inject_time <= case.time_end:
                continue
            report = build_benchmark_report(case, model)
            table = load_metrics(CACHE / case.case / "metrics.parquet")
            valid, total = verify_ledger(report, table)
            ranks = report["ranking"]
            lead = report["hypotheses"][0]
            rows.append({
                "case": case.case,
                "correct": ranks["learned_lead"] == case.root_cause_service,
                "agree": ranks["learned_lead"] == ranks["statistical_lead"],
                "margin": ranks["learned_margin"],
                "valid_citations": valid,
                "citations": total,
                "claim_review": review_claims(report, table, case.inject_time),
                "lead_contradicted": any(entry["relation"] == "contradicting" for entry in lead["evidence"]),
            })
        claims = Counter()
        for row in rows:
            claims.update(row["claim_review"])
        output[dataset] = {
            "summary": {**summarize(rows), "claim_review": dict(claims),
                        "contradiction_ablation": contradiction_ablation(rows)},
            "cases": rows,
        }
    return output


if __name__ == "__main__":
    result = run()
    path = Path("reports/evidence-audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for dataset, report in result.items():
        print(dataset, {key: value for key, value in report["summary"].items() if key != "risk_coverage"})
