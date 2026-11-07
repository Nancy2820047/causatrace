import json
from pathlib import Path
import unittest

from scripts.evidence_gap import Observation, investigate


class EvidenceGapTest(unittest.TestCase):
    def run_fixture(self, name: str) -> dict:
        root = Path(__file__).resolve().parents[1]
        incident = json.loads((root / "data" / "demo" / f"{name}.json").read_text())
        observations = [Observation(**item) for item in incident["observations"]]
        report = investigate(observations)
        for hypothesis in report["hypotheses"]:
            for record in hypothesis["evidence"]:
                self.assertIn(record["observation_id"], {item.id for item in observations})
        return report

    def test_earlier_symptom_gives_a_lead_and_challenges_the_alternative(self) -> None:
        report = self.run_fixture("demo-001")
        self.assertEqual(report["status"], "LEADING_HYPOTHESIS")
        self.assertEqual(report["hypotheses"][0]["service"], "orders-db")
        counter = report["hypotheses"][1]["evidence"][1]
        self.assertEqual(counter["relation"], "contradicting")

    def test_tie_requests_a_specific_missing_check(self) -> None:
        report = self.run_fixture("demo-002")
        self.assertEqual(report["status"], "NEEDS_INVESTIGATION")
        self.assertEqual(report["next_check"]["signal"], "connection_pool_saturation")
        self.assertEqual(report["next_check"]["availability"], "missing")

    def test_rejects_ambiguous_citations(self) -> None:
        item = Observation("same", "2026-01-01T10:00:00Z", "db", "errors", 1)
        with self.assertRaisesRegex(ValueError, "unique"):
            investigate([item, item])
