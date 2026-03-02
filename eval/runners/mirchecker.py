"""Runner for tools/mirchecker/run_mir_checker.ps1."""

from __future__ import annotations

from pathlib import Path

try:
    from ..config import TOOLS_ROOT
except ImportError:
    from config import TOOLS_ROOT

from .base import BaseRunner


class MirCheckerRunner(BaseRunner):
    """Invoke MirChecker with testcase path adaptation."""

    def __init__(self, timeout_seconds: int | float | None = None) -> None:
        tool_root = (TOOLS_ROOT / "mirchecker").resolve()
        script_path = tool_root / "run_mir_checker.ps1"
        super().__init__(
            tool_name="MirChecker",
            tool_root=tool_root,
            script_path=script_path,
            timeout_seconds=timeout_seconds,
        )
        self._staging_root = self.tool_root / "tests" / "_eval_runner"

    def run(self, case_path: Path, case_id: str) -> dict:
        source = self._normalize_case_path(case_path)
        if not source.exists():
            return self._precheck_failed(f"[MirChecker] case path not found: {source}")

        target = self._prepare_case(source, case_id)
        return self._run_script(["-Target", target])

    def _prepare_case(self, source: Path, case_id: str) -> str:
        source = source.resolve()
        if self._is_inside_tool_root(source):
            return self._to_tool_relative_path(source)

        target_name = self._safe_case_name(case_id, fallback=source.name)
        if source.is_file() and source.suffix and (
            not target_name.lower().endswith(source.suffix.lower())
        ):
            target_name = f"{target_name}{source.suffix}"

        staged = self._staging_root / target_name
        self._sync_path(source, staged)
        return self._to_tool_relative_path(staged)
