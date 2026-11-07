"""Evaluate service rankings on grouped Online Boutique fault injections."""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import random
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scripts.inspect_rcaeval import CACHE, REVISION, SOURCE, download_sample, load_metrics, verify


@dataclass(frozen=True)
class Case:
    case: str
    root_cause_service: str
    fault: str
    inject_time: int
    time_start: int
    time_end: int


def cases_and_splits() -> dict[str, list[Case]]:
    verify((CACHE / 'cases.parquet').read_bytes(), 'cases.parquet')
    columns = list(Case.__annotations__)
    rows = pq.read_table(CACHE / "cases.parquet", columns=columns, filters=[
        ("dataset", "=", "RE1-OB"),
    ]).to_pylist()
    cases = [Case(**row) for row in rows]
    by_time = sorted(cases, key=lambda case: case.time_start)
    if len(cases) != 125 or any(
        left.time_end >= right.time_start for left, right in zip(by_time, by_time[1:])
    ):
        raise ValueError("Unexpected case count or overlapping capture windows")

    groups = defaultdict(list)
    for case in cases:
        groups[case.fault, case.root_cause_service].append(case)
    by_fault = defaultdict(list)
    for fault, service in sorted(groups):
        by_fault[fault].append(service)

    splits = {"train": [], "validation": [], "test": []}
    rng = random.Random(42)
    for fault, services in sorted(by_fault.items()):
        if len(services) != 5:
            raise ValueError(f"Expected five service groups for {fault}")
        rng.shuffle(services)
        for service, split in zip(services, ["train"] * 3 + ["validation", "test"]):
            splits[split].extend(sorted(groups[fault, service], key=lambda case: case.case))
    return splits


def fetch_metrics(case: Case) -> None:
    target = CACHE / case.case / "metrics.parquet"
    if target.exists():
        return
    with urlopen(f"{SOURCE}/{case.case}/metrics.parquet", timeout=30) as response:
        data = response.read(4_000_001)
    if len(data) > 4_000_000 or not data.startswith(b"PAR1") or not data.endswith(b"PAR1"):
        raise ValueError(f"Invalid or oversized Parquet response for {case.case}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        pending = Path(temporary.name)
    try:
        pending.write_bytes(data)
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)


def extract_features(
    metrics: pa.Table, alert_time: int, post_start: int = 0, post_end: int = 120,
) -> tuple[list[str], np.ndarray, dict[str, dict]]:
    """Use only telemetry and a supplied alert time to score candidate services."""
    time = metrics["time"].to_numpy()
    before = (time >= alert_time - 120) & (time < alert_time)
    after = (time >= alert_time + post_start) & (time < alert_time + post_end)
    if not before.any() or not after.any():
        raise ValueError("The alert needs both a baseline and an observation window")
    by_service = defaultdict(list)
    evidence = {}
    for column in metrics.column_names[1:]:
        service, separator, _ = column.partition("_")
        if not separator:
            raise ValueError(f"Expected a service_signal metric name: {column}")
        values = metrics[column].to_numpy()
        baseline = values[before]
        observed = values[after]
        baseline = baseline[np.isfinite(baseline)]
        valid = np.isfinite(observed)
        if not baseline.size or not valid.any():
            continue
        center = np.median(baseline)
        scale = max(1.4826 * np.median(np.abs(baseline - center)), abs(center) * 0.01, 1e-9)
        change = np.clip(np.abs(observed[valid] - center) / scale, 0, 100)
        hits = np.flatnonzero(valid)[change >= 3]
        magnitude = float(np.quantile(change, 0.95))
        by_service[service].append([
            magnitude,
            np.mean(change >= 3),
            1 - hits[0] / len(observed) if len(hits) else 0,
        ])
        if service not in evidence or magnitude > evidence[service]["magnitude"]:
            peak = np.flatnonzero(after)[np.flatnonzero(valid)[int(np.argmax(change))]]
            evidence[service] = {
                "id": f"{column}:{peak}",
                "service": service,
                "signal": column,
                "timestamp": int(time[peak]),
                "value": float(values[peak]),
                "row_index": int(peak),
                "baseline_median": float(center),
                "magnitude": magnitude,
            }
    services = sorted(by_service)
    if not services:
        raise ValueError("No candidate service has usable metric data")
    values = np.array([np.max(by_service[service], axis=0) for service in services])
    return services, values, evidence


def features(
    metrics: pa.Table, alert_time: int, post_start: int = 0, post_end: int = 120,
) -> tuple[list[str], np.ndarray]:
    services, values, _ = extract_features(metrics, alert_time, post_start, post_end)
    return services, values


def fit_ranker(train):
    x = np.vstack([values for _, _, values in train])
    y = [service == case.root_cause_service for case, services, _ in train for service in services]
    model = make_pipeline(StandardScaler(), LogisticRegression(
        class_weight="balanced", random_state=42, max_iter=1000,
    ))
    return model.fit(x, y)


def evaluate(download: bool) -> dict:
    if download:
        download_sample(CACHE)
    splits = cases_and_splits()
    if download:
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(fetch_metrics, [case for split in splits.values() for case in split]))

    prepared = {}
    fingerprints = {}
    excluded = {}
    for split, cases in splits.items():
        prepared[split] = []
        for case in cases:
            path = CACHE / case.case / "metrics.parquet"
            fingerprints[case.case] = sha256(path.read_bytes()).hexdigest()
            metrics = load_metrics(path)
            if (metrics["time"][0].as_py(), metrics["time"][-1].as_py()) != (
                case.time_start, case.time_end
            ):
                raise ValueError(f"Capture bounds differ from index for {case.case}")
            if not case.time_start < case.inject_time <= case.time_end:
                excluded[case.case] = 'Injection time is outside the recorded window'
                continue
            services, values = features(metrics, case.inject_time)
            prepared[split].append((case, services, values))
    if len(set(fingerprints.values())) != len(fingerprints):
        raise ValueError("Duplicate metric files found")

    model = fit_ranker(prepared["train"])

    results = {}
    for split in ("validation", "test"):
        rows = []
        for case, services, values in prepared[split]:
            scores = {
                "rule": values[:, 2],
                "statistical": values[:, 0],
                "learned": model.decision_function(values),
            }
            orders = {
                name: [services[index] for index in np.argsort(-score, kind="stable")]
                for name, score in scores.items()
            }
            rows.append({
                "case": case.case,
                "fault": case.fault,
                "label": case.root_cause_service,
                "predictions": {name: order[:3] for name, order in orders.items()},
                "ranks": {
                    name: order.index(case.root_cause_service) + 1
                    if case.root_cause_service in order else None
                    for name, order in orders.items()
                },
            })
        summary = {}
        for name in ("rule", "statistical", "learned"):
            ranks = [row["ranks"][name] for row in rows]
            summary[name] = {
                "top_1": sum(rank == 1 for rank in ranks) / len(rows),
                "top_3": sum(rank is not None and rank <= 3 for rank in ranks) / len(rows),
                "mrr": sum(1 / rank for rank in ranks if rank is not None) / len(rows),
            }
        results[split] = {"summary": summary, "cases": rows}
    return {
        "dataset": "RE1-OB",
        "revision": REVISION,
        "alert": "fault injection time used as a proxy",
        "window_seconds_each_side": 120,
        "split_seed": 42,
        "splits": {name: [case.case for case in cases] for name, cases in splits.items()},
        "metrics_sha256": fingerprints,
        "excluded_cases": excluded,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Cache all 125 RE1-OB metric files")
    parser.add_argument("--output", type=Path, default=Path("reports/re1-ob.json"))
    args = parser.parse_args()
    try:
        result = evaluate(args.download)
    except FileNotFoundError as error:
        parser.exit(1, f"Benchmark file is missing. Run with --download. {error}\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Benchmark error: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for split, results in result["results"].items():
        print(split, json.dumps(results["summary"]))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
