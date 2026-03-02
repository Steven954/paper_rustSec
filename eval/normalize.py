"""Normalize raw analyzer outputs into one CSV for downstream analysis."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Callable

try:
    from config import RESULTS_DIR
    from load_cases import load_cases
    from parsers import parse_ffichecker, parse_mirchecker, parse_rudra
    from parsers._common import split_raw_result
except ImportError:
    from .config import RESULTS_DIR
    from .load_cases import load_cases
    from .parsers import parse_ffichecker, parse_mirchecker, parse_rudra
    from .parsers._common import split_raw_result

INVALID_FILENAME_CHARS = '<>:"/\\|?*'
OUTPUT_FIELDS = [
    "case_id",
    "scenario",
    "tool",
    "run_status",
    "detected",
    "alert_count",
    "alerts_json",
    "duration_sec",
]

PARSER_BY_TOOL: dict[str, Callable[[str, str], dict[str, Any]]] = {
    "rudra": parse_rudra,
    "mirchecker": parse_mirchecker,
    "ffichecker": parse_ffichecker,
}


def _safe_filename(value: str) -> str:
    safe = (value or "").strip()
    for ch in INVALID_FILENAME_CHARS:
        safe = safe.replace(ch, "_")
    safe = safe.rstrip(" .")
    return safe or "case"


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _parse_float(value: Any) -> float:
    try:
        return float(str(value or "0").strip())
    except (TypeError, ValueError):
        return 0.0


def _run_status_from_log(row: dict[str, Any]) -> str:
    timeout = _parse_bool(row.get("timeout"))
    success = _parse_bool(row.get("success"))
    if timeout:
        return "timeout"
    if success:
        return "success"
    return "error"


def _load_scenarios() -> dict[str, str]:
    scenarios: dict[str, str] = {}
    try:
        for case in load_cases():
            case_id = str(case.get("id", "")).strip()
            scenario = str(case.get("scenario", "")).strip()
            if case_id:
                scenarios[case_id] = scenario
    except Exception:
        return {}
    return scenarios


def _normalize_alerts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def _parse_raw_result(tool: str, raw_path: Path) -> tuple[bool, list[dict[str, Any]]]:
    parser = PARSER_BY_TOOL.get(tool.lower())
    if parser is None:
        raise KeyError(f"Unsupported tool parser: {tool}")

    content = raw_path.read_text(encoding="utf-8", errors="replace")
    raw_output, raw_stderr = split_raw_result(content)
    parsed = parser(raw_output, raw_stderr) or {}
    alerts = _normalize_alerts(parsed.get("alerts"))
    detected = bool(parsed.get("detected", False))
    return detected, alerts


def _build_row(
    row: dict[str, Any],
    scenario_map: dict[str, str],
    raw_dir: Path,
) -> dict[str, Any]:
    case_id = str(row.get("case_id", "")).strip()
    tool = str(row.get("tool", "")).strip()
    duration = _parse_float(row.get("duration", row.get("duration_sec", 0.0)))

    run_status = _run_status_from_log(row)
    detected = False
    alerts: list[dict[str, Any]] = []

    raw_name = f"{_safe_filename(tool)}_{_safe_filename(case_id)}.txt"
    raw_path = (raw_dir / raw_name).resolve()

    if not raw_path.is_file():
        run_status = "error"
    else:
        try:
            detected, alerts = _parse_raw_result(tool=tool, raw_path=raw_path)
        except Exception:
            run_status = "error"
            detected = False
            alerts = []

    return {
        "case_id": case_id,
        "scenario": scenario_map.get(case_id, ""),
        "tool": tool,
        "run_status": run_status,
        "detected": detected,
        "alert_count": len(alerts),
        "alerts_json": json.dumps(alerts, ensure_ascii=False),
        "duration_sec": f"{duration:.6f}",
    }


def normalize(
    run_log_path: Path,
    raw_dir: Path,
    output_path: Path,
) -> int:
    if not run_log_path.is_file():
        raise FileNotFoundError(f"run_log.csv not found: {run_log_path}")

    scenario_map = _load_scenarios()

    with run_log_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    normalized_rows = [_build_row(row, scenario_map, raw_dir) for row in rows]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_rows)

    print(f"Normalized records: {len(normalized_rows)}")
    print(f"Output written: {output_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize eval/results raw outputs into normalized.csv."
    )
    parser.add_argument(
        "--run-log",
        default=str((RESULTS_DIR / "run_log.csv").resolve()),
        help="Path to run_log.csv",
    )
    parser.add_argument(
        "--raw-dir",
        default=str((RESULTS_DIR / "raw").resolve()),
        help="Path to raw output directory",
    )
    parser.add_argument(
        "--output",
        default=str((RESULTS_DIR / "normalized.csv").resolve()),
        help="Path to normalized.csv",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return normalize(
        run_log_path=Path(args.run_log).resolve(),
        raw_dir=Path(args.raw_dir).resolve(),
        output_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
