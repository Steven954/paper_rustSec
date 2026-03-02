"""Base runner abstraction for tool invocation."""

from __future__ import annotations

import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

try:
    from ..config import PROJECT_ROOT, TIMEOUT_SECONDS
except ImportError:
    from config import PROJECT_ROOT, TIMEOUT_SECONDS


class BaseRunner(ABC):
    """Common execution helper for all tool runners."""

    def __init__(
        self,
        tool_name: str,
        tool_root: Path,
        script_path: Path,
        timeout_seconds: int | float | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.project_root = PROJECT_ROOT
        self.tool_root = tool_root.resolve()
        self.script_path = script_path.resolve()
        self.timeout_seconds = float(
            TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )

        if not self.script_path.is_file():
            raise FileNotFoundError(
                f"[{self.tool_name}] script not found: {self.script_path}"
            )

    @abstractmethod
    def run(self, case_path: Path, case_id: str) -> dict:
        """Run the tool on one testcase and return a normalized result dict."""

    def _run_script(self, script_args: Sequence[str]) -> dict:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.script_path),
            *script_args,
        ]

        start = time.perf_counter()
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(self.tool_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start
            stdout = self._coerce_text(exc.stdout)
            stderr = self._coerce_text(exc.stderr)
            timeout_msg = (
                f"[{self.tool_name}] timed out after {self.timeout_seconds:.1f}s."
            )
            stderr = f"{stderr}\n{timeout_msg}".strip()
            return self._result(
                success=False,
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                duration_sec=duration,
                timeout=True,
            )
        except OSError as exc:
            duration = time.perf_counter() - start
            return self._result(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"[{self.tool_name}] failed to execute script: {exc}",
                duration_sec=duration,
                timeout=False,
            )

        duration = time.perf_counter() - start
        return self._result(
            success=(completed.returncode == 0),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_sec=duration,
            timeout=False,
        )

    def _normalize_case_path(self, case_path: Path) -> Path:
        raw_path = Path(case_path)
        if not raw_path.is_absolute():
            raw_path = self.project_root / raw_path
        return raw_path.resolve()

    def _precheck_failed(self, message: str) -> dict:
        return self._result(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=message,
            duration_sec=0.0,
            timeout=False,
        )

    def _is_inside_tool_root(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.tool_root)
            return True
        except ValueError:
            return False

    def _to_tool_relative_path(self, path: Path) -> str:
        rel = path.resolve().relative_to(self.tool_root)
        return str(rel).replace("/", "\\")

    def _sync_path(self, source: Path, target: Path) -> None:
        source = source.resolve()
        target = target.resolve()

        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if not target.exists():
                shutil.copytree(source, target)
                return

            if not target.is_dir():
                target.unlink()
                shutil.copytree(source, target)
                return

            for child in source.iterdir():
                # Keep staged build cache to support incremental compilation.
                if child.name == "target":
                    continue

                child_target = target / child.name
                if child_target.exists():
                    if child_target.is_dir():
                        shutil.rmtree(child_target)
                    else:
                        child_target.unlink()

                if child.is_dir():
                    shutil.copytree(child, child_target)
                else:
                    shutil.copy2(child, child_target)
            return

        if target.exists() and target.is_dir():
            shutil.rmtree(target)
        shutil.copy2(source, target)

    @staticmethod
    def _safe_case_name(case_id: str, fallback: str) -> str:
        base = (case_id or "").strip() or fallback
        invalid = '<>:"/\\|?*'
        for ch in invalid:
            base = base.replace(ch, "_")
        return base.rstrip(" .") or "case"

    @staticmethod
    def _coerce_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    @staticmethod
    def _result(
        success: bool,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_sec: float,
        timeout: bool,
    ) -> dict:
        return {
            "success": bool(success),
            "exit_code": int(exit_code),
            "stdout": stdout or "",
            "stderr": stderr or "",
            "duration_sec": round(float(duration_sec), 6),
            "timeout": bool(timeout),
        }
