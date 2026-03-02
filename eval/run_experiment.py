"""Run evaluation tools over testcase combinations and persist raw outputs."""

from __future__ import annotations

import argparse
import csv
import time
import traceback
from pathlib import Path

try:
    from config import PROJECT_ROOT, RESULTS_DIR
    from load_cases import load_cases
    from runners import FFICheckerRunner, MirCheckerRunner, RudraRunner
except ImportError:
    from .config import PROJECT_ROOT, RESULTS_DIR
    from .load_cases import load_cases
    from .runners import FFICheckerRunner, MirCheckerRunner, RudraRunner

INVALID_FILENAME_CHARS = '<>:"/\\|?*'

TOOL_SPECS = {
    "rudra": ("Rudra", RudraRunner),
    "mirchecker": ("MirChecker", MirCheckerRunner),
    "ffichecker": ("FFIChecker", FFICheckerRunner),
}


def _safe_filename(value: str) -> str:
    safe = (value or "").strip()
    for ch in INVALID_FILENAME_CHARS:
        safe = safe.replace(ch, "_")
    safe = safe.rstrip(" .")
    return safe or "case"


def _split_csv_values(values: list[str] | None) -> list[str]:
    if not values:
        return []

    items: list[str] = []
    for raw in values:
        for item in raw.split(","):
            cleaned = item.strip()
            if cleaned:
                items.append(cleaned)
    return items


def _parse_tools(values: list[str] | None) -> list[str]:
    requested = _split_csv_values(values)
    if not requested:
        return list(TOOL_SPECS.keys())

    invalid: list[str] = []
    selected: list[str] = []
    for item in requested:
        key = item.lower()
        if key not in TOOL_SPECS:
            invalid.append(item)
            continue
        if key not in selected:
            selected.append(key)

    if invalid:
        valid = ", ".join(TOOL_SPECS.keys())
        bad = ", ".join(invalid)
        raise ValueError(f"Unknown tools: {bad}. Valid choices: {valid}")
    if not selected:
        raise ValueError("No valid tools selected.")
    return selected


def _select_cases(all_cases: list[dict], cases_arg: str | None) -> list[dict]:
    if cases_arg is None:
        return all_cases

    raw = cases_arg.strip()
    if not raw:
        raise ValueError("--cases cannot be empty.")

    if raw.isdigit():
        limit = int(raw)
        if limit <= 0:
            raise ValueError("--cases numeric value must be > 0.")
        return all_cases[:limit]

    wanted = [item.strip() for item in raw.split(",") if item.strip()]
    if not wanted:
        raise ValueError("No valid case IDs provided in --cases.")

    case_by_id = {case["id"]: case for case in all_cases}
    missing = [case_id for case_id in wanted if case_id not in case_by_id]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Unknown case IDs in --cases: {missing_text}")

    return [case_by_id[case_id] for case_id in wanted]


def _normalize_result(result: dict | None) -> dict:
    data = result or {}
    return {
        "success": bool(data.get("success", False)),
        "exit_code": int(data.get("exit_code", -1)),
        "stdout": str(data.get("stdout", "") or ""),
        "stderr": str(data.get("stderr", "") or ""),
        "duration_sec": float(data.get("duration_sec", 0.0) or 0.0),
        "timeout": bool(data.get("timeout", False)),
    }


def _format_raw_output(case_id: str, tool: str, result: dict) -> str:
    stdout = result.get("stdout", "") or ""
    stderr = result.get("stderr", "") or ""
    lines = [
        f"case_id: {case_id}",
        f"tool: {tool}",
        f"success: {result.get('success', False)}",
        f"exit_code: {result.get('exit_code', -1)}",
        f"duration_sec: {result.get('duration_sec', 0.0):.6f}",
        f"timeout: {result.get('timeout', False)}",
        "",
        "===== STDOUT =====",
        stdout,
        "",
        "===== STDERR =====",
        stderr,
    ]
    return "\n".join(lines)


def _write_raw_result(raw_dir: Path, tool: str, case_id: str, result: dict) -> Path:
    filename = f"{_safe_filename(tool)}_{_safe_filename(case_id)}.txt"
    output_path = (raw_dir / filename).resolve()
    content = _format_raw_output(case_id=case_id, tool=tool, result=result)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _write_run_log(log_path: Path, records: list[dict]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case_id", "tool", "success", "duration", "timeout"],
        )
        writer.writeheader()
        writer.writerows(records)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run all (case, tool) experiments.")
    parser.add_argument(
        "--tools",
        action="append",
        help="Tool list, comma-separated. e.g. rudra,mirchecker,ffichecker",
    )
    parser.add_argument(
        "--cases",
        help="Case selection: number N for first N cases, or comma-separated case IDs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned combinations without executing runners.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        selected_tools = _parse_tools(args.tools)
    except ValueError as exc:
        parser.error(str(exc))

    all_cases = load_cases()
    try:
        selected_cases = _select_cases(all_cases, args.cases)
    except ValueError as exc:
        parser.error(str(exc))

    raw_dir = (RESULTS_DIR / "raw").resolve()
    log_path = (RESULTS_DIR / "run_log.csv").resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)

    total = len(selected_cases) * len(selected_tools)
    print(f"Selected tools: {', '.join(selected_tools)}")
    print(f"Selected cases: {len(selected_cases)}")
    print(f"Total combinations: {total}")

    records: list[dict] = []
    if args.dry_run:
        index = 0
        for case in selected_cases:
            case_id = case["id"]
            for tool in selected_tools:
                index += 1
                print(f"[DRY-RUN {index}/{total}] tool={tool}, case_id={case_id}")

        _write_run_log(log_path, records)
        print(f"Dry-run complete. Log written: {log_path}")
        return 0

    init_failures: dict[str, str] = {}
    runners: dict[str, object] = {}
    for tool in selected_tools:
        display_name, runner_cls = TOOL_SPECS[tool]
        try:
            runners[tool] = runner_cls()
        except Exception:
            init_failures[tool] = traceback.format_exc()
            print(f"[INIT FAILED] tool={tool} ({display_name})")

    index = 0
    for case in selected_cases:
        case_id = case["id"]
        case_path = (PROJECT_ROOT / case["path"]).resolve()

        for tool in selected_tools:
            index += 1
            print(f"[{index}/{total}] Running tool={tool}, case_id={case_id}")

            if not case_path.exists():
                result = _normalize_result(
                    {
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": f"[run_experiment] case path not found: {case_path}",
                        "duration_sec": 0.0,
                        "timeout": False,
                    }
                )
            elif tool in init_failures:
                result = _normalize_result(
                    {
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": init_failures[tool],
                        "duration_sec": 0.0,
                        "timeout": False,
                    }
                )
            else:
                runner = runners[tool]
                start = time.perf_counter()
                try:
                    run_output = runner.run(case_path, case_id=case_id)
                except Exception:
                    duration = time.perf_counter() - start
                    run_output = {
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": traceback.format_exc(),
                        "duration_sec": duration,
                        "timeout": False,
                    }
                result = _normalize_result(run_output)

            raw_path = _write_raw_result(raw_dir, tool, case_id, result)
            records.append(
                {
                    "case_id": case_id,
                    "tool": tool,
                    "success": result["success"],
                    "duration": f"{result['duration_sec']:.6f}",
                    "timeout": result["timeout"],
                }
            )
            print(
                "  -> "
                f"success={result['success']}, "
                f"duration={result['duration_sec']:.6f}s, "
                f"timeout={result['timeout']}, "
                f"raw={raw_path}"
            )

    _write_run_log(log_path, records)
    print(f"Completed runs: {len(records)}")
    print(f"Run log written: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
