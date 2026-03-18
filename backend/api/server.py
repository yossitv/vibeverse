from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.services.pipeline import DemoPipelineRunner
from backend.services.storage import LocalJobStore


def build_handler(
    store: LocalJobStore,
    pipeline: DemoPipelineRunner,
) -> type[BaseHTTPRequestHandler]:
    class VibeVerseRequestHandler(BaseHTTPRequestHandler):
        server_version = "VibeVerseHTTP/0.1"

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_common_headers()
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]

            try:
                if parsed.path == "/health":
                    self._send_json(HTTPStatus.OK, {"status": "ok"})
                    return

                if parts == ["api", "jobs"]:
                    self._send_json(HTTPStatus.OK, {"jobs": store.list_jobs()})
                    return

                if len(parts) >= 3 and parts[0] == "api" and parts[1] == "jobs":
                    job_id = parts[2]
                    if len(parts) == 3:
                        self._send_json(HTTPStatus.OK, {"job": store.get_job(job_id)})
                        return
                    if len(parts) == 4 and parts[3] == "status":
                        job = store.get_job(job_id)
                        payload = {
                            "job_id": job["job_id"],
                            "status": job["status"],
                            "updated_at": job["updated_at"],
                            "error": job["error"],
                            "events": job["events"],
                        }
                        self._send_json(HTTPStatus.OK, payload)
                        return
                    if len(parts) == 4 and parts[3] == "chat":
                        job = store.get_job(job_id)
                        payload = {
                            "job_id": job["job_id"],
                            "status": job["status"],
                            "messages": job["messages"],
                        }
                        self._send_json(HTTPStatus.OK, payload)
                        return
                    if len(parts) == 4 and parts[3] == "asset":
                        job = store.get_job(job_id)
                        payload = {
                            "job_id": job["job_id"],
                            "status": job["status"],
                            "asset": job["asset"],
                            "paths": job["paths"],
                        }
                        self._send_json(HTTPStatus.OK, payload)
                        return

                self._send_error_json(HTTPStatus.NOT_FOUND, "Route not found.")
            except KeyError:
                self._send_error_json(HTTPStatus.NOT_FOUND, "Job not found.")
            except Exception as exc:  # pragma: no cover - defensive path
                self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]

            try:
                if parts == ["api", "jobs"]:
                    payload = self._read_json()
                    prompt = str(payload.get("prompt", "")).strip()
                    if not prompt:
                        self._send_error_json(HTTPStatus.BAD_REQUEST, "Field 'prompt' is required.")
                        return
                    job = store.create_job(prompt)
                    pipeline.run_async(job["job_id"])
                    self._send_json(
                        HTTPStatus.ACCEPTED,
                        {
                            "job": job,
                            "poll_url": f"/api/jobs/{job['job_id']}",
                            "status_url": f"/api/jobs/{job['job_id']}/status",
                            "chat_url": f"/api/jobs/{job['job_id']}/chat",
                            "asset_url": f"/api/jobs/{job['job_id']}/asset",
                        },
                    )
                    return

                if len(parts) == 4 and parts[0] == "api" and parts[1] == "jobs" and parts[3] == "placed":
                    job = store.mark_placed(parts[2])
                    self._send_json(HTTPStatus.OK, {"job": job})
                    return

                self._send_error_json(HTTPStatus.NOT_FOUND, "Route not found.")
            except ValueError as exc:
                self._send_error_json(HTTPStatus.CONFLICT, str(exc))
            except KeyError:
                self._send_error_json(HTTPStatus.NOT_FOUND, "Job not found.")
            except json.JSONDecodeError:
                self._send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
            except Exception as exc:  # pragma: no cover - defensive path
                self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _read_json(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length)
            return json.loads(body.decode("utf-8"))

        def _send_json(self, status: int | HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self._send_common_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error_json(self, status: int | HTTPStatus, message: str) -> None:
            self._send_json(status, {"error": message})

        def _send_common_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    return VibeVerseRequestHandler


def create_server(
    root_dir: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    step_delay: float = 0.15,
) -> ThreadingHTTPServer:
    store = LocalJobStore(root_dir)
    pipeline = DemoPipelineRunner(store, step_delay=step_delay)
    handler = build_handler(store, pipeline)
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the VibeVerse backend API.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    parser.add_argument(
        "--root-dir",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root directory.",
    )
    args = parser.parse_args()

    server = create_server(root_dir=args.root_dir, host=args.host, port=args.port)
    print(f"VibeVerse backend API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
