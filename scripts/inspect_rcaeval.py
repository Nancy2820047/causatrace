"""Read a pinned RCAEval RE1 sample and keep its evaluation labels separate."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
CASE = "re1ob_adservice_cpu_1"
SOURCE = f"https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/{REVISION}"
FILES = {
    "cases.parquet": (
        29_500, "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb",
    ),
    f"{CASE}/metrics.parquet": (
        368_024, "464dcc215afe145d37f8b107ea291df7ffc0691756d375c54ddc1c09d0a2ac74",
    ),
}
CACHE = Path(__file__).resolve().parents[1] / "data" / "raw" / "rcaeval" / REVISION


@dataclass(frozen=True)
class EvaluationLabel:
    source_case: str
    root_cause_service: str
    fault: str
    injection_time: int


def verify(data: bytes, source_path: str) -> bytes:
    size, digest = FILES[source_path]
    if len(data) != size or sha256(data).hexdigest() != digest:
        raise ValueError(f"Size or SHA-256 mismatch for {source_path}")
    return data


def download_sample(cache: Path) -> None:
    for source_path, (size, _) in FILES.items():
        target = cache / source_path
        if target.exists():
            verify(target.read_bytes(), source_path)
            continue

        with urlopen(f"{SOURCE}/{source_path}", timeout=30) as response:
            data = verify(response.read(size + 1), source_path)

        target.parent.mkdir(parents=True, exist_ok=True)
        # Publish the verified file only after the write completes.
        with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            pending = Path(temporary.name)
        try:
            pending.write_bytes(data)
            pending.replace(target)
        finally:
            pending.unlink(missing_ok=True)


def load_metrics(path: Path) -> pa.Table:
    table = pq.read_table(path)
    names = table.column_names
    if len(names) < 2 or names[0] != "time" or len(names) != len(set(names)):
        raise ValueError("Expected a time column followed by uniquely named metrics")
    time = table["time"]
    if time.type != pa.int64() or not len(time) or time.null_count:
        raise ValueError("Expected nonempty, non-null int64 Unix timestamps")
    if pc.any(pc.less_equal(time.slice(1), time.slice(0, len(time) - 1))).as_py():
        raise ValueError("Metric timestamps must be strictly increasing")
    if any(field.type != pa.float64() for field in list(table.schema)[1:]):
        raise ValueError("Expected float64 metric columns")
    return table.replace_schema_metadata(None)


def load_label(index: Path, case_id: str) -> EvaluationLabel:
    columns = ["case", "root_cause_service", "fault", "inject_time"]
    matches = pq.read_table(index, columns=columns, filters=[("case", "=", case_id)])
    if matches.num_rows != 1:
        raise ValueError(f"Expected exactly one evaluation label for {case_id}")
    row = matches.to_pylist()[0]
    return EvaluationLabel(case_id, row["root_cause_service"], row["fault"], row["inject_time"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch the pinned 398 KB sample")
    args = parser.parse_args()

    try:
        if args.download:
            download_sample(CACHE)
        for source_path in FILES:
            verify((CACHE / source_path).read_bytes(), source_path)
        metrics = load_metrics(CACHE / CASE / "metrics.parquet")
        label = load_label(CACHE / "cases.parquet", CASE)
    except FileNotFoundError as error:
        parser.exit(1, f"Missing benchmark file. Run with --download. {error}\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Benchmark sample error: {error}\n")

    time = metrics["time"]
    print(f"{metrics.num_rows:,} metric samples, {metrics.num_columns - 1} signals")
    print(f"UTC epoch seconds: {time[0].as_py()} to {time[-1].as_py()}")
    print("Modalities: metrics available, logs and traces absent")
    print(f"Evaluation label: {label.root_cause_service} / {label.fault}")
    print(f"Injection time (evaluation metadata): {label.injection_time}")


if __name__ == "__main__":
    main()
