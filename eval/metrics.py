"""Compute evaluation metrics from normalized results."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import RESULTS_DIR
    from load_cases import load_cases
except ImportError:
    from .config import RESULTS_DIR
    from .load_cases import load_cases

SCENARIO_ORDER = ("S1", "S2", "S3", "S4")


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


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _scenario_sort_key(scenario: str) -> tuple[int, str]:
    if scenario in SCENARIO_ORDER:
        return (SCENARIO_ORDER.index(scenario), scenario)
    return (len(SCENARIO_ORDER), scenario)


def _build_case_maps() -> tuple[set[str], dict[str, str], dict[str, list[str]]]:
    case_ids: set[str] = set()
    case_to_scenario: dict[str, str] = {}
    scenario_to_cases: dict[str, list[str]] = {}

    for case in load_cases():
        case_id = str(case.get("id", "")).strip()
        scenario = str(case.get("scenario", "")).strip()
        if not case_id:
            continue

        case_ids.add(case_id)
        case_to_scenario[case_id] = scenario
        scenario_to_cases.setdefault(scenario, []).append(case_id)

    for scenario, ids in scenario_to_cases.items():
        ids.sort()

    return case_ids, case_to_scenario, scenario_to_cases


def _read_normalized_rows(normalized_path: Path) -> list[dict[str, Any]]:
    if not normalized_path.is_file():
        raise FileNotFoundError(f"normalized.csv not found: {normalized_path}")

    with normalized_path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_records(
    rows: list[dict[str, Any]],
    valid_case_ids: set[str],
    case_to_scenario: dict[str, str],
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str], int, int]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    tools: list[str] = []
    ignored_rows = 0
    duplicate_rows = 0

    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        tool = str(row.get("tool", "")).strip().lower()
        if not case_id or not tool:
            ignored_rows += 1
            continue
        if case_id not in valid_case_ids:
            ignored_rows += 1
            continue

        if tool not in tools:
            tools.append(tool)

        key = (tool, case_id)
        if key in records:
            duplicate_rows += 1

        records[key] = {
            "tool": tool,
            "case_id": case_id,
            "scenario": case_to_scenario.get(case_id, ""),
            "run_status": str(row.get("run_status", "")).strip().lower(),
            "detected": _parse_bool(row.get("detected")),
            "duration_sec": _parse_float(row.get("duration_sec")),
        }

    return records, tools, ignored_rows, duplicate_rows


def _compute_by_tool(
    tools: list[str],
    case_ids: set[str],
    records: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    total_cases = len(case_ids)
    by_tool: dict[str, dict[str, Any]] = {}

    for tool in tools:
        success_cases = 0
        detected_cases = 0
        durations: list[float] = []

        for case_id in case_ids:
            rec = records.get((tool, case_id))
            if rec is None:
                continue
            durations.append(rec["duration_sec"])
            if rec["run_status"] == "success":
                success_cases += 1
            if rec["detected"]:
                detected_cases += 1

        avg_duration = sum(durations) / len(durations) if durations else 0.0
        by_tool[tool] = {
            "total_cases": total_cases,
            "observed_rows": len(durations),
            "success_cases": success_cases,
            "detected_cases": detected_cases,
            "executability_rate": _safe_ratio(success_cases, total_cases),
            "recall": _safe_ratio(detected_cases, total_cases),
            "avg_duration_sec": avg_duration,
        }

    return by_tool


def _compute_by_tool_scenario(
    tools: list[str],
    scenario_to_cases: dict[str, list[str]],
    records: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]:
    by_tool_scenario: dict[str, dict[str, dict[str, Any]]] = {}
    csv_rows: list[dict[str, Any]] = []

    scenarios = sorted(scenario_to_cases.keys(), key=_scenario_sort_key)

    for tool in tools:
        tool_bucket: dict[str, dict[str, Any]] = {}
        for scenario in scenarios:
            case_ids = scenario_to_cases.get(scenario, [])
            total_cases = len(case_ids)
            success_cases = 0
            detected_cases = 0

            for case_id in case_ids:
                rec = records.get((tool, case_id))
                if rec is None:
                    continue
                if rec["run_status"] == "success":
                    success_cases += 1
                if rec["detected"]:
                    detected_cases += 1

            item = {
                "total_cases": total_cases,
                "success_cases": success_cases,
                "detected_cases": detected_cases,
                "executability_rate": _safe_ratio(success_cases, total_cases),
                "recall": _safe_ratio(detected_cases, total_cases),
            }
            tool_bucket[scenario] = item
            csv_rows.append(
                {
                    "tool": tool,
                    "scenario": scenario,
                    **item,
                }
            )

        by_tool_scenario[tool] = tool_bucket

    return by_tool_scenario, csv_rows


def _write_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_scenario_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "tool",
        "scenario",
        "total_cases",
        "success_cases",
        "detected_cases",
        "executability_rate",
        "recall",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _print_metrics(summary: dict[str, Any], scenario_rows: list[dict[str, Any]]) -> None:
    print(f"Cases from load_cases: {summary['total_cases']}")
    print(f"Rows in normalized.csv: {summary['normalized_rows_total']}")
    print(f"Rows used for metrics: {summary['normalized_rows_used']}")
    print(f"Ignored rows: {summary['ignored_rows']}")
    print(f"Duplicate rows overwritten: {summary['duplicate_rows_overwritten']}")

    tools = summary["tools"]
    if not tools:
        print("No tool rows found in normalized.csv.")
        return

    print("\nBy tool:")
    for tool in tools:
        m = summary["by_tool"][tool]
        print(
            f"- {tool}: "
            f"executability={m['executability_rate']:.4f} "
            f"({m['success_cases']}/{m['total_cases']}), "
            f"recall={m['recall']:.4f} "
            f"({m['detected_cases']}/{m['total_cases']}), "
            f"avg_duration_sec={m['avg_duration_sec']:.6f}"
        )

    print("\nBy tool/scenario:")
    for row in scenario_rows:
        print(
            f"- tool={row['tool']}, scenario={row['scenario']}, "
            f"executability={row['executability_rate']:.4f} "
            f"({row['success_cases']}/{row['total_cases']}), "
            f"recall={row['recall']:.4f} "
            f"({row['detected_cases']}/{row['total_cases']})"
        )


def compute_metrics(
    normalized_path: str | Path | None = None,
    summary_output_path: str | Path | None = None,
    scenario_output_path: str | Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Compute metrics and write summary files.

    Returns a dictionary for report integration.
    """
    normalized_csv = Path(
        normalized_path or (RESULTS_DIR / "normalized.csv").resolve()
    ).resolve()
    summary_json = Path(
        summary_output_path or (RESULTS_DIR / "metrics_summary.json").resolve()
    ).resolve()
    scenario_csv = Path(
        scenario_output_path or (RESULTS_DIR / "metrics_by_scenario.csv").resolve()
    ).resolve()

    case_ids, case_to_scenario, scenario_to_cases = _build_case_maps()
    normalized_rows = _read_normalized_rows(normalized_csv)
    records, tools, ignored_rows, duplicate_rows = _build_records(
        rows=normalized_rows,
        valid_case_ids=case_ids,
        case_to_scenario=case_to_scenario,
    )

    by_tool = _compute_by_tool(tools=tools, case_ids=case_ids, records=records)
    by_tool_scenario, scenario_rows = _compute_by_tool_scenario(
        tools=tools,
        scenario_to_cases=scenario_to_cases,
        records=records,
    )

    summary: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "normalized_path": str(normalized_csv),
        "total_cases": len(case_ids),
        "cases_by_scenario": {
            scenario: len(ids)
            for scenario, ids in sorted(
                scenario_to_cases.items(), key=lambda item: _scenario_sort_key(item[0])
            )
        },
        "normalized_rows_total": len(normalized_rows),
        "normalized_rows_used": len(records),
        "ignored_rows": ignored_rows,
        "duplicate_rows_overwritten": duplicate_rows,
        "tools": tools,
        "by_tool": by_tool,
        "by_tool_scenario": by_tool_scenario,
        "outputs": {
            "metrics_summary_json": str(summary_json),
            "metrics_by_scenario_csv": str(scenario_csv),
        },
    }

    _write_summary_json(summary_json, summary)
    _write_scenario_csv(scenario_csv, scenario_rows)

    if verbose:
        _print_metrics(summary, scenario_rows)
        print(f"\nSummary JSON written: {summary_json}")
        print(f"Scenario CSV written: {scenario_csv}")

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute metrics from normalized.csv.")
    parser.add_argument(
        "--normalized",
        default=str((RESULTS_DIR / "normalized.csv").resolve()),
        help="Path to normalized.csv",
    )
    parser.add_argument(
        "--summary-output",
        default=str((RESULTS_DIR / "metrics_summary.json").resolve()),
        help="Path to metrics_summary.json",
    )
    parser.add_argument(
        "--scenario-output",
        default=str((RESULTS_DIR / "metrics_by_scenario.csv").resolve()),
        help="Path to metrics_by_scenario.csv",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print computed metrics.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    compute_metrics(
        normalized_path=Path(args.normalized).resolve(),
        summary_output_path=Path(args.summary_output).resolve(),
        scenario_output_path=Path(args.scenario_output).resolve(),
        verbose=not args.quiet,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
