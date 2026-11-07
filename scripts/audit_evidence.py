"""Check raw evidence references and compare selective rankings."""

import json
from datetime import datetime
from pathlib import Path

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
            rows.append({
                "case": case.case,
                "correct": ranks["learned_lead"] == case.root_cause_service,
                "agree": ranks["learned_lead"] == ranks["statistical_lead"],
                "margin": ranks["learned_margin"],
                "valid_citations": valid,
                "citations": total,
            })
        output[dataset] = {"summary": summarize(rows), "cases": rows}
    return output


if __name__ == "__main__":
    result = run()
    path = Path("reports/evidence-audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for dataset, report in result.items():
        print(dataset, {key: value for key, value in report["summary"].items() if key != "risk_coverage"})
