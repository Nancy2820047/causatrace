"""Serve the offline CausaTrace investigation demo on loopback."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from scripts.evidence_gap import Observation, investigate


ROOT = Path(__file__).resolve().parents[1]
INCIDENTS = ("demo-001", "demo-002")


def load_report(incident_id: str) -> dict:
    if incident_id not in INCIDENTS:
        raise KeyError(incident_id)
    source = ROOT / "data" / "demo" / f"{incident_id}.json"
    incident = json.loads(source.read_text(encoding="utf-8"))
    observations = [Observation(**item) for item in incident["observations"]]
    return {**incident, **investigate(observations)}


def markdown(report: dict) -> str:
    lines = [
        f"# {report['incident_id']}", "", f"**Status:** {report['status']}",
        "", report["reason"], "", "## Hypotheses",
    ]
    observations = {item["id"]: item for item in report["observations"]}
    for hypothesis in report["hypotheses"]:
        lines.extend(["", f"### {hypothesis['service']}"])
        for record in hypothesis["evidence"]:
            item = observations[record["observation_id"]]
            lines.append(
                f"- {record['relation']} | {item['id']} | {item['timestamp']} | "
                f"{item['service']} / {item['signal']} = {item['value']} | {item.get('file', '')} | {record['reason']}"
            )
    if check := report["next_check"]:
        lines.extend([
            "", "## Next check",
            f"- {check['service']} / {check['signal']} ({check['availability']})",
            f"- {check['start']} to {check['end_exclusive']} (end exclusive)",
            f"- {check['purpose']}",
        ])
    if source := report.get("source"):
        lines.extend([
            "", "## Source",
            f"- {source['dataset']} / {source['case']} / {source['file']}",
            f"- Revision {source['revision']}",
        ])
    lines.extend(["", "## Limitations"])
    if report["synthetic"]:
        lines.append("- Synthetic demo incident.")
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    benchmark_report: dict | None = None

    def reply(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def json_reply(self, payload: dict, status: int = 200) -> None:
        self.reply(json.dumps(payload).encode(), "application/json", status)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self.reply((ROOT / "app" / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/api/incidents":
            incident_ids = list(INCIDENTS)
            if self.benchmark_report:
                incident_ids.append(self.benchmark_report["incident_id"])
            self.json_reply({"incidents": incident_ids})
            return
        prefix = "/api/incidents/"
        if path.startswith(prefix):
            incident_id = path.removeprefix(prefix)
            markdown_requested = incident_id.endswith(".md")
            try:
                incident_id = incident_id.removesuffix(".md")
                if self.benchmark_report and incident_id == self.benchmark_report["incident_id"]:
                    report = self.benchmark_report
                else:
                    report = load_report(incident_id)
            except KeyError:
                self.json_reply({"error": "Unknown incident"}, 404)
                return
            if markdown_requested:
                self.reply(markdown(report).encode(), "text/markdown; charset=utf-8")
            else:
                self.json_reply(report)
            return
        self.json_reply({"error": "Unknown route"}, 404)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--benchmark", action="store_true", help="Also load the cached RE1 benchmark")
    parser.add_argument("--train-ticket", action="store_true", help="Load the cached RE2 multimodal case")
    args = parser.parse_args()
    if args.train_ticket:
        try:
            from scripts.train_ticket import load_report as load_train_ticket

            Handler.benchmark_report = load_train_ticket()
        except (ImportError, OSError, ValueError) as error:
            parser.exit(1, f"Train Ticket unavailable. See docs/DATASETS.md. {error}\n")
    elif args.benchmark:
        try:
            from scripts.benchmark_investigation import load_benchmark_report

            Handler.benchmark_report = load_benchmark_report()
        except (ImportError, OSError, ValueError) as error:
            parser.exit(1, f"Benchmark unavailable. See docs/EVALUATION.md. {error}\n")
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Open http://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
