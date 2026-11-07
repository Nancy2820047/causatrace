import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen
import unittest

from scripts.serve_demo import Handler


class InvestigationApiTest(unittest.TestCase):
    def test_dashboard_data_exports_and_unknown_incident(self) -> None:
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base, timeout=5) as response:
                    self.assertIn(b"CausaTrace | Incident explorer", response.read())
                with urlopen(base + "/api/incidents", timeout=5) as response:
                    self.assertEqual(json.load(response)["incidents"], ["demo-001", "demo-002"])
                with urlopen(base + "/api/incidents/demo-002", timeout=5) as response:
                    report = json.load(response)
                    self.assertEqual(report["status"], "NEEDS_INVESTIGATION")
                    self.assertEqual(report["next_check"]["availability"], "missing")
                with urlopen(base + "/api/incidents/demo-001.md", timeout=5) as response:
                    self.assertIn(b"obs-001", response.read())
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/incidents/unknown", timeout=5)
                self.assertEqual(error.exception.code, 404)
                error.exception.close()
            finally:
                server.shutdown()
                worker.join(timeout=5)
