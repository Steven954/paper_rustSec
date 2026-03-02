"""Run selected tools on selected cases and inspect raw outputs."""

from __future__ import annotations

import re
import traceback
from pathlib import Path

try:
    from config import PROJECT_ROOT, RESULTS_DIR, TESTCASES_ROOT
    from load_cases import load_cases
    from runners import FFICheckerRunner, MirCheckerRunner, RudraRunner
except ImportError:
    from .config import PROJECT_ROOT, RESULTS_DIR, TESTCASES_ROOT
    from .load_cases import load_cases
    from .runners import FFICheckerRunner, MirCheckerRunner, RudraRunner


TARGET_CASE_IDS = [
    "examples__c-in-rust-doublefree",
    "tests__panic_safety__order_unsafe.rs",
    "cases__panic_double_free",
]

KEYWORDS = [
    "error",
    "warning",
    "bug",
    "unsafe",
    "panic",
    "vulnerability",
    "detected",
]

FILE_LINE_PATTERN = re.compile(
    r"(?im)\b(?:[A-Za-z]:)?[^\s:]+(?:[\\/][^\s:]+)*\.[A-Za-z0-9_]+:\d+(?::\d+)?\b"
)
LINE_NUMBER_PATTERN = re.compile(r"(?im)\bline\s+\d+\b")
INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def _safe_filename(value: str) -> str:
    safe = (value or "").strip()
    for ch in INVALID_FILENAME_CHARS:
        safe = safe.replace(ch, "_")
    safe = safe.rstrip(" .")
    return safe or "case"


def _is_supported(tool_name: str, case_path: Path) -> tuple[bool, str]:
    if tool_name == "FFIChecker":
        if case_path.is_dir() and (case_path / "Cargo.toml").is_file():
            return True, ""
        return False, "FFIChecker only supports Cargo project directories with Cargo.toml."
    return True, ""


def _line_count(text: str) -> int:
    return len((text or "").splitlines())


def _keyword_hits(stdout: str, stderr: str) -> dict[str, bool]:
    merged = f"{stdout}\n{stderr}".lower()
    return {kw: (kw in merged) for kw in KEYWORDS}


def _has_line_reference(stdout: str, stderr: str) -> bool:
    merged = f"{stdout}\n{stderr}"
    return bool(FILE_LINE_PATTERN.search(merged) or LINE_NUMBER_PATTERN.search(merged))


def _resolve_case_path(case_id: str, loaded_map: dict[str, dict]) -> Path | None:
    case_meta = loaded_map.get(case_id)
    if case_meta is not None:
        path = (PROJECT_ROOT / case_meta["path"]).resolve()
        if path.exists():
            return path

    fallback = (TESTCASES_ROOT / case_id).resolve()
    if fallback.exists():
        return fallback
    return None


def _build_runners() -> tuple[list[tuple[str, object]], list[dict]]:
    specs = [
        ("Rudra", RudraRunner),
        ("MirChecker", MirCheckerRunner),
        ("FFIChecker", FFICheckerRunner),
    ]
    runners: list[tuple[str, object]] = []
    init_issues: list[dict] = []

    for tool_name, runner_cls in specs:
        try:
            runners.append((tool_name, runner_cls()))
        except Exception:
            init_issues.append(
                {
                    "tool": tool_name,
                    "case_id": "-",
                    "status": "init_error",
                    "reason": traceback.format_exc(),
                    "stdout_path": None,
                    "stderr_path": None,
                }
            )
    return runners, init_issues


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")


def main() -> int:
    inspect_dir = (RESULTS_DIR / "inspect").resolve()
    inspect_dir.mkdir(parents=True, exist_ok=True)

    loaded_cases = load_cases()
    loaded_map = {case["id"]: case for case in loaded_cases}

    runners, records = _build_runners()
    output_files: list[Path] = []

    for case_id in TARGET_CASE_IDS:
        case_path = _resolve_case_path(case_id, loaded_map)
        if case_path is None:
            for tool_name, _ in runners:
                records.append(
                    {
                        "tool": tool_name,
                        "case_id": case_id,
                        "status": "missing_case",
                        "reason": f"Case path not found for {case_id}",
                        "stdout_path": None,
                        "stderr_path": None,
                    }
                )
            continue

        for tool_name, runner in runners:
            supported, reason = _is_supported(tool_name, case_path)
            if not supported:
                records.append(
                    {
                        "tool": tool_name,
                        "case_id": case_id,
                        "status": "skipped_unsupported",
                        "reason": reason,
                        "stdout_path": None,
                        "stderr_path": None,
                    }
                )
                continue

            try:
                result = runner.run(case_path, case_id=case_id)
            except Exception:
                result = {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": traceback.format_exc(),
                    "duration_sec": 0.0,
                    "timeout": False,
                }

            safe_case_id = _safe_filename(case_id)
            base_name = f"{tool_name}_{safe_case_id}"
            stdout_path = (inspect_dir / f"{base_name}_stdout.txt").resolve()
            stderr_path = (inspect_dir / f"{base_name}_stderr.txt").resolve()

            stdout_text = result.get("stdout", "") or ""
            stderr_text = result.get("stderr", "") or ""
            _write_text(stdout_path, stdout_text)
            _write_text(stderr_path, stderr_text)

            output_files.extend([stdout_path, stderr_path])

            records.append(
                {
                    "tool": tool_name,
                    "case_id": case_id,
                    "status": "ran",
                    "success": bool(result.get("success", False)),
                    "exit_code": int(result.get("exit_code", -1)),
                    "duration_sec": float(result.get("duration_sec", 0.0)),
                    "timeout": bool(result.get("timeout", False)),
                    "stdout_path": stdout_path,
                    "stderr_path": stderr_path,
                    "stdout_lines": _line_count(stdout_text),
                    "stderr_lines": _line_count(stderr_text),
                    "keyword_hits": _keyword_hits(stdout_text, stderr_text),
                    "has_line_reference": _has_line_reference(stdout_text, stderr_text),
                }
            )

    print("Saved output files:")
    if output_files:
        for path in output_files:
            print(f"- {path}")
    else:
        print("- (none)")

    print("\nSummary:")
    for rec in records:
        tool = rec["tool"]
        case_id = rec["case_id"]
        status = rec["status"]
        print("-" * 80)
        print(f"tool={tool}, case_id={case_id}, status={status}")

        if status != "ran":
            print(f"reason={rec.get('reason', '')}")
            print("stdout_lines=N/A")
            print("stderr_lines=N/A")
            print("keywords=N/A")
            print("has_line_reference=N/A")
            continue

        print(f"success={rec['success']}, exit_code={rec['exit_code']}, timeout={rec['timeout']}, duration_sec={rec['duration_sec']:.6f}")
        print(f"stdout_path={rec['stdout_path']}")
        print(f"stderr_path={rec['stderr_path']}")
        print(f"stdout_lines={rec['stdout_lines']}")
        print(f"stderr_lines={rec['stderr_lines']}")
        print(f"keywords={rec['keyword_hits']}")
        print(f"has_line_reference={rec['has_line_reference']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
