from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.api.server import create_server


class BackendAPITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.server = create_server(self.temp_dir.name, port=0, step_delay=0.01)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def test_create_job_and_export_asset(self) -> None:
        created = self._request_json(
            "POST",
            "/api/jobs",
            {"prompt": "create an Nvidia-themed event prop for Roblox"},
            expected_status=202,
        )

        job_id = created["job"]["job_id"]
        exported = self._wait_for_status(job_id, "exported")
        self.assertEqual(exported["status"], "exported")

        asset = self._request_json("GET", f"/api/jobs/{job_id}/asset")
        export_path = Path(asset["paths"]["export_path"])
        metadata_path = Path(asset["paths"]["metadata_path"])
        self.assertTrue(export_path.exists())
        self.assertTrue(metadata_path.exists())

        placed = self._request_json("POST", f"/api/jobs/{job_id}/placed")
        self.assertEqual(placed["job"]["status"], "placed")

        chat = self._request_json("GET", f"/api/jobs/{job_id}/chat")
        self.assertGreaterEqual(len(chat["messages"]), 2)

    def test_rejects_empty_prompt(self) -> None:
        response = self._request_json(
            "POST",
            "/api/jobs",
            {"prompt": "   "},
            expected_status=400,
        )
        self.assertIn("error", response)

    def _wait_for_status(self, job_id: str, expected_status: str, timeout: float = 3.0) -> dict:
        deadline = time.monotonic() + timeout
        last = {}
        while time.monotonic() < deadline:
            last = self._request_json("GET", f"/api/jobs/{job_id}/status")
            if last.get("status") == expected_status:
                return last
            time.sleep(0.02)
        self.fail(f"Timed out waiting for {expected_status!r}, last payload: {last}")

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        expected_status: int = 200,
    ) -> dict:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, expected_status)
                return json.loads(body)
        except HTTPError as exc:
            body = exc.read().decode("utf-8")
            self.assertEqual(exc.code, expected_status)
            return json.loads(body)


if __name__ == "__main__":
    unittest.main()
