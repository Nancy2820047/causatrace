import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.inspect_rcaeval import load_label, load_metrics, verify


class BenchmarkAdapterTest(unittest.TestCase):
    def test_metrics_and_labels_are_loaded_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            metrics = folder / "metrics.parquet"
            index = folder / "cases.parquet"
            pq.write_table(pa.table({"time": [10, 11], "service_cpu": [0.1, 0.4]}), metrics)
            pq.write_table(
                pa.table({
                    "case": ["service_cpu_1"],
                    "root_cause_service": ["service"],
                    "fault": ["cpu"],
                    "inject_time": [11],
                }),
                index,
            )

            self.assertEqual(load_metrics(metrics).column_names, ["time", "service_cpu"])
            self.assertEqual(load_label(index, "service_cpu_1").root_cause_service, "service")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                load_label(index, "missing")

    def test_duplicate_timestamps_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metrics = Path(directory) / "metrics.parquet"
            pq.write_table(pa.table({"time": [10, 10], "service_cpu": [0.1, 0.4]}), metrics)
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                load_metrics(metrics)

    def test_bad_checksum_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify(b"x" * 29_500, "cases.parquet")
