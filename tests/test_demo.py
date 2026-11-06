from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = PROJECT_ROOT / "scripts" / "run_demo.py"


class DemoSmokeTest(unittest.TestCase):
    def check_demo(
        self, arguments: list[str], incident_id: str, evidence_ids: tuple[str, str]
    ) -> None:
        result = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT), *arguments],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[:1], [f"Incident: {incident_id} (synthetic)"])
        self.assertEqual(
            [line.split(" | ", 1)[0] for line in lines[1:]],
            list(evidence_ids),
        )

    def test_default_incident(self) -> None:
        self.check_demo([], "demo-001", ("obs-001", "obs-002"))

    def test_select_second_incident(self) -> None:
        self.check_demo(["demo-002"], "demo-002", ("obs-003", "obs-004"))
