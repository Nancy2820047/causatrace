import unittest

import pyarrow as pa

from scripts.audit_evidence import contradiction_ablation, review_claims, summarize, verify_ledger


class EvidenceAuditTest(unittest.TestCase):
    def test_valid_reference_can_have_an_unsupported_baseline_claim(self) -> None:
        table = pa.table({"time": [9, 10], "api_cpu": [1.0, 1.5]})
        report = {
            "observations": [{
                "id": "api_cpu:1", "signal": "api_cpu", "row_index": 1,
                "timestamp": "1970-01-01T00:00:10+00:00", "value": 1.5,
                "service": "api", "baseline_median": 1.0, "magnitude": 50.0,
            }],
            "hypotheses": [{"service": "api", "evidence": [
                {"observation_id": "api_cpu:1", "relation": "supporting"},
            ]}],
        }
        self.assertEqual(review_claims(report, table, 10)["supporting_passed"], 1)
        report["observations"][0]["baseline_median"] = 0.5
        self.assertEqual(verify_ledger(report, table), (1, 1))
        self.assertEqual(review_claims(report, table, 10)["supporting_passed"], 0)

    def test_ablation_holds_the_answer_budget_fixed(self) -> None:
        rows = [
            {"case": "a", "margin": 2.0, "correct": True, "lead_contradicted": True},
            {"case": "b", "margin": 1.0, "correct": False, "lead_contradicted": False},
        ]
        self.assertEqual(contradiction_ablation(rows), {
            "eligible": 2, "answered_per_arm": 1,
            "correct_with_contradiction_check": 0, "correct_with_margin_only": 1,
        })

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
