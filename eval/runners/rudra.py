"""Runner for tools/Rudra/run_rudra.ps1."""

from __future__ import annotations

from pathlib import Path

try:
    from ..config import TOOLS_ROOT
except ImportError:
    from config import TOOLS_ROOT

from .base import BaseRunner


class RudraRunner(BaseRunner):
    """Invoke Rudra with testcase path adaptation."""

    def __init__(self, timeout_seconds: int | float | None = None) -> None:
        tool_root = (TOOLS_ROOT / "Rudra").resolve()
        script_path = tool_root / "run_rudra.ps1"
        super().__init__(
            tool_name="Rudra",
            tool_root=tool_root,
            script_path=script_path,
            timeout_seconds=timeout_seconds,
        )
        self._staging_tests_root = self.tool_root / "tests" / "_eval_runner"
        self._staging_cases_root = self.tool_root / "cases" / "_eval_runner"

    def run(self, case_path: Path, case_id: str) -> dict:
        source = self._normalize_case_path(case_path)
        if not source.exists():
            return self._precheck_failed(f"[Rudra] case path not found: {source}")

        target = self._prepare_case(source, case_id)
        return self._run_script(["-Case", target])

    def _prepare_case(self, source: Path, case_id: str) -> str:
        source = source.resolve()
        if self._is_inside_tool_root(source):
            rel = self._to_tool_relative_path(source)
            rel_lower = rel.lower()
            if rel_lower.startswith("tests\\") or rel_lower.startswith("cases\\"):
                return rel

        if source.is_file():
            target_name = self._safe_case_name(case_id, fallback=source.name)
            if source.suffix and not target_name.lower().endswith(source.suffix.lower()):
                target_name = f"{target_name}{source.suffix}"
            staged = self._staging_tests_root / target_name
        else:
            target_name = self._safe_case_name(case_id, fallback=source.name)
            staged = self._staging_cases_root / target_name

        self._sync_path(source, staged)
        return self._to_tool_relative_path(staged)
