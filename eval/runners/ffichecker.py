"""Runner for tools/FFIChecker/run_ffi_checker.ps1."""

from __future__ import annotations

from pathlib import Path

try:
    from ..config import TOOLS_ROOT
except ImportError:
    from config import TOOLS_ROOT

from .base import BaseRunner


class FFICheckerRunner(BaseRunner):
    """Invoke FFIChecker with testcase path adaptation."""

    def __init__(self, timeout_seconds: int | float | None = None) -> None:
        tool_root = (TOOLS_ROOT / "FFIChecker").resolve()
        script_path = tool_root / "run_ffi_checker.ps1"
        super().__init__(
            tool_name="FFIChecker",
            tool_root=tool_root,
            script_path=script_path,
            timeout_seconds=timeout_seconds,
        )
        self._staging_root = self.tool_root / "examples" / "_eval_runner"

    def run(self, case_path: Path, case_id: str) -> dict:
        source = self._normalize_case_path(case_path)
        if not source.exists():
            return self._precheck_failed(f"[FFIChecker] case path not found: {source}")

        target = self._prepare_case(source, case_id)
        return self._run_script(["-Target", target])

    def _prepare_case(self, source: Path, case_id: str) -> str:
        source = source.resolve()
        if self._is_inside_tool_root(source):
            return self._to_tool_relative_path(source)

        # FFIChecker effectively analyzes a Cargo project directory.
        if source.is_dir():
            source_for_tool = source
        else:
            source_for_tool = self._find_cargo_project_root(source.parent) or source.parent

        target_name = self._safe_case_name(case_id, fallback=source_for_tool.name)
        staged = self._staging_root / target_name
        self._sync_path(source_for_tool, staged)
        return self._to_tool_relative_path(staged)

    @staticmethod
    def _find_cargo_project_root(start_dir: Path) -> Path | None:
        current = start_dir.resolve()
        while True:
            if (current / "Cargo.toml").is_file():
                return current

            parent = current.parent
            if parent == current:
                return None
            current = parent
