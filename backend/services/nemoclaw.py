from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from backend.services.storage import LocalJobStore, append_assistant_message, append_event

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class NemoClawExecutor:
    def __init__(
        self,
        openshell_bin: str = "openshell",
        ssh_bin: str = "ssh",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.openshell_bin = openshell_bin
        self.ssh_bin = ssh_bin
        self.timeout_seconds = timeout_seconds

    def run(self, prompt: str, session_id: str, sandbox_name: str) -> str:
        if not prompt.strip():
            raise RuntimeError("Prompt must not be empty.")

        if shutil.which(self.openshell_bin) is None:
            raise RuntimeError(f"{self.openshell_bin} is not available on PATH.")
        if shutil.which(self.ssh_bin) is None:
            raise RuntimeError(f"{self.ssh_bin} is not available on PATH.")

        ssh_config = self._build_ssh_config(sandbox_name)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(ssh_config)
            config_path = Path(handle.name)

        try:
            remote_cmd = (
                "nemoclaw-start openclaw agent --agent main --local "
                f"-m {shlex.quote(prompt)} --session-id {shlex.quote(session_id)}"
            )
            result = subprocess.run(
                [
                    self.ssh_bin,
                    "-T",
                    "-F",
                    str(config_path),
                    f"openshell-{sandbox_name}",
                    remote_cmd,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=self._command_env(),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"NemoClaw request timed out after {self.timeout_seconds:.0f} seconds."
            ) from exc
        finally:
            config_path.unlink(missing_ok=True)

        response = self._extract_response(result.stdout)
        if response:
            return response

        stderr = self._clean_output(result.stderr).strip()
        if result.returncode != 0:
            detail = stderr or "no stderr output"
            raise RuntimeError(f"NemoClaw command failed with exit code {result.returncode}: {detail}")
        raise RuntimeError("NemoClaw returned no response.")

    def _build_ssh_config(self, sandbox_name: str) -> str:
        result = subprocess.run(
            [self.openshell_bin, "sandbox", "ssh-config", sandbox_name],
            capture_output=True,
            text=True,
            env=self._command_env(),
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            detail = self._clean_output(result.stderr).strip() or "no stderr output"
            raise RuntimeError(f"Failed to resolve sandbox SSH config for {sandbox_name!r}: {detail}")
        return result.stdout

    def _command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        local_bin = str(Path.home() / ".local" / "bin")
        current_path = env.get("PATH", "")
        if local_bin not in current_path.split(":"):
            env["PATH"] = f"{local_bin}:{current_path}" if current_path else local_bin
        return env

    def _extract_response(self, output: str) -> str:
        lines: list[str] = []
        for raw_line in self._clean_output(output).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("Setting up NemoClaw"):
                continue
            if line.startswith("[gateway]"):
                continue
            if line.startswith("(node:"):
                continue
            if line.startswith("sandbox@"):
                continue
            if line.startswith("🦞 OpenClaw"):
                continue
            if line.startswith("Self-hosted, self-updating"):
                continue
            if line.startswith("[plugins]"):
                continue
            if "plugins.allow is empty" in line:
                continue
            if "NemoClaw registered" in line:
                continue
            if line.startswith("Endpoint:"):
                continue
            if line.startswith("Model:"):
                continue
            if line.startswith("Commands:"):
                continue
            if line.startswith("┌") or line.startswith("│") or line.startswith("└"):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _clean_output(self, text: str) -> str:
        return ANSI_ESCAPE_RE.sub("", text.replace("\r", ""))


class NemoClawJobRunner:
    def __init__(
        self,
        store: LocalJobStore,
        executor: NemoClawExecutor,
        default_sandbox_name: str = "my-assistant",
    ) -> None:
        self.store = store
        self.executor = executor
        self.default_sandbox_name = default_sandbox_name

    def run_async(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()

    def _run_job(self, job_id: str) -> None:
        try:
            job = self.store.mutate_job(job_id, self._mark_running)
            sandbox_name = job["assistant"]["sandbox_name"] or self.default_sandbox_name
            session_id = job["assistant"]["session_id"]
            prompt = job["prompt"]

            response = self.executor.run(
                prompt=prompt,
                session_id=session_id,
                sandbox_name=sandbox_name,
            )

            def complete(job_state: dict[str, object]) -> None:
                job_state["status"] = "completed"
                assistant = job_state.setdefault("assistant", {})
                assistant["sandbox_name"] = sandbox_name
                assistant["response"] = response
                append_event(
                    job_state,
                    "completed",
                    "assistant_completed",
                    f"NemoClaw returned a response from sandbox '{sandbox_name}'.",
                )
                append_assistant_message(job_state, response)

            self.store.mutate_job(job_id, complete)
            self.store.sync_asset_metadata(job_id)
        except Exception as exc:  # pragma: no cover - defensive path
            def fail(job_state: dict[str, object]) -> None:
                job_state["status"] = "failed"
                job_state["error"] = str(exc)
                append_event(
                    job_state,
                    "failed",
                    "assistant_failed",
                    f"NemoClaw failed: {exc}",
                )
                append_assistant_message(job_state, f"NemoClaw failed: {exc}")

            self.store.mutate_job(job_id, fail)
            self.store.sync_asset_metadata(job_id)

    def _mark_running(self, job: dict[str, object]) -> None:
        assistant = job.setdefault("assistant", {})
        sandbox_name = assistant.get("sandbox_name") or self.default_sandbox_name
        assistant["sandbox_name"] = sandbox_name
        job["status"] = "running"
        append_event(
            job,
            "running",
            "assistant_started",
            f"Forwarded request to NemoClaw sandbox '{sandbox_name}'.",
        )
        append_assistant_message(job, f"Forwarded request to NemoClaw sandbox '{sandbox_name}'.")
