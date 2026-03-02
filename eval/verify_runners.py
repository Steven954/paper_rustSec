"""Quick verification script for Rudra/MirChecker/FFIChecker runners."""

from __future__ import annotations

import traceback
from pathlib import Path

try:
    from config import PROJECT_ROOT
    from load_cases import load_cases
    from runners import FFICheckerRunner, MirCheckerRunner, RudraRunner
except ImportError:
    from .config import PROJECT_ROOT
    from .load_cases import load_cases
    from .runners import FFICheckerRunner, MirCheckerRunner, RudraRunner


PREFERRED_DIR_CASE_ID = "examples__c-in-rust-doublefree"
PREFERRED_FILE_CASE_ID = "tests__panic_safety__order_unsafe.rs"
PRINT_LIMIT = 500


def _truncate(text: str, limit: int = PRINT_LIMIT) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n... (truncated, total={len(text)} chars)"


def _pick_case(cases: list[dict], preferred_id: str, want_dir: bool) -> dict | None:
    by_id = {c.get("id"): c for c in cases}
    preferred = by_id.get(preferred_id)
    if preferred:
        preferred_path = (PROJECT_ROOT / preferred["path"]).resolve()
        if want_dir and preferred_path.is_dir():
            return preferred
        if (not want_dir) and preferred_path.is_file():
            return preferred

    for case in cases:
        case_path = (PROJECT_ROOT / case["path"]).resolve()
        if want_dir and case_path.is_dir():
            return case
        if (not want_dir) and case_path.is_file():
            return case
    return None


def _is_supported(tool_name: str, case_abs_path: Path) -> tuple[bool, str]:
    if tool_name == "FFIChecker":
        if case_abs_path.is_dir() and (case_abs_path / "Cargo.toml").is_file():
            return True, ""
        return False, "FFIChecker only supports Cargo project directories with Cargo.toml."
    return True, ""


def _print_result(case_id: str, tool: str, result: dict) -> None:
    print("-" * 80)
    print(f"case_id: {case_id}")
    print(f"tool: {tool}")
    print(f"success: {result.get('success')}")
    print(f"exit_code: {result.get('exit_code')}")
    print(f"duration_sec: {result.get('duration_sec')}")
    print(f"timeout: {result.get('timeout')}")
    print("stdout_head_500:")
    print(_truncate(result.get("stdout", "")))
    print("stderr_head_500:")
    print(_truncate(result.get("stderr", "")))


def main() -> int:
    cases = load_cases()
    dir_case = _pick_case(cases, PREFERRED_DIR_CASE_ID, want_dir=True)
    file_case = _pick_case(cases, PREFERRED_FILE_CASE_ID, want_dir=False)

    if dir_case is None or file_case is None:
        print("Cannot select verification cases: missing directory or single-file case.")
        return 2

    selected_cases = [dir_case, file_case]
    print("Selected cases:")
    for case in selected_cases:
        abs_path = (PROJECT_ROOT / case["path"]).resolve()
        kind = "dir" if abs_path.is_dir() else "file"
        print(f"- {case['id']} [{kind}] -> {abs_path}")

    runners = [
        ("Rudra", RudraRunner()),
        ("MirChecker", MirCheckerRunner()),
        ("FFIChecker", FFICheckerRunner()),
    ]

    for case in selected_cases:
        case_id = case["id"]
        case_abs_path = (PROJECT_ROOT / case["path"]).resolve()

        for tool_name, runner in runners:
            supported, reason = _is_supported(tool_name, case_abs_path)
            if not supported:
                print("-" * 80)
                print(f"case_id: {case_id}")
                print(f"tool: {tool_name}")
                print("skip: True")
                print(f"reason: {reason}")
                continue

            try:
                result = runner.run(case_abs_path, case_id=case_id)
            except Exception:
                result = {
                    "success": False,
                    "exit_code": -1,
                    "duration_sec": 0.0,
                    "timeout": False,
                    "stdout": "",
                    "stderr": traceback.format_exc(),
                }
            _print_result(case_id, tool_name, result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
