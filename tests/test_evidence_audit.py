import unittest

import pyarrow as pa

from scripts.audit_evidence import summarize, verify_ledger


class EvidenceAuditTest(unittest.TestCase):
    def test_verifier_rejects_a_citation_with_a_changed_value(self) -> None:
        table = pa.table({"time": [10], "api_cpu": [0.2]})
        observation = {
            "id": "api_cpu:0",
            "signal": "api_cpu",
            "row_index": 0,
            "timestamp": "1970-01-01T00:00:10+00:00",
            "value": 0.2,
        }
        report = {
            "observations": [observation],
            "hypotheses": [{"evidence": [{"observation_id": "api_cpu:0"}]}],
        }
        self.assertEqual(verify_ledger(report, table), (1, 1))
        observation["value"] = 0.3
        self.assertEqual(verify_ledger(report, table), (0, 1))

    def test_risk_curve_keeps_equal_margins_together(self) -> None:
        rows = [
            {"margin": 1, "correct": value, "agree": False, "valid_citations": 1, "citations": 1}
            for value in (True, False)
        ]
        result = summarize(rows)
        self.assertEqual(result["risk_coverage"], [{"answered": 2, "coverage": 1.0, "risk": 0.5}])
        self.assertIsNone(result["agreement_answered_accuracy"])
