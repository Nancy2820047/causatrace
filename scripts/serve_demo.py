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
                f"{item['service']} / {item['signal']} = {item['value']} | {record['reason']}"
            )
    if check := report["next_check"]:
        lines.extend([
            "", "## Next check",
            f"- {check['service']} / {check['signal']} ({check['availability']})",
            f"- {check['start']} to {check['end_exclusive']} (end exclusive)",
            f"- {check['purpose']}",
        ])
    lines.extend(["", "## Limitations", "- Synthetic demo incident."])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
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
            self.json_reply({"incidents": INCIDENTS})
            return
        prefix = "/api/incidents/"
        if path.startswith(prefix):
            incident_id = path.removeprefix(prefix)
            markdown_requested = incident_id.endswith(".md")
            try:
                report = load_report(incident_id.removesuffix(".md"))
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
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Open http://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
