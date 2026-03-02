"""Run full evaluation on all configured cases and tools."""

from __future__ import annotations

import argparse
import csv
import time
import traceback
from pathlib import Path
from typing import Any

try:
    from config import RESULTS_DIR, PROJECT_ROOT
    from load_cases import load_cases
    from metrics import compute_metrics
    from normalize import normalize
    from report import generate_report
    from run_experiment import (
        TOOL_SPECS,
        _normalize_result,
        _parse_tools,
        _select_cases,
        _write_raw_result,
        _write_run_log,
    )
except ImportError:
    from .config import RESULTS_DIR, PROJECT_ROOT
    from .load_cases import load_cases
    from .metrics import compute_metrics
    from .normalize import normalize
    from .report import generate_report
    from .run_experiment import (
        TOOL_SPECS,
        _normalize_result,
        _parse_tools,
        _select_cases,
        _write_raw_result,
        _write_run_log,
    )

DEFAULT_TOOLS = ("rudra", "mirchecker", "ffichecker")

KNOWN_DETECTION_EXPECTATIONS: dict[str, dict[str, bool | None]] = {
    "examples__c-in-rust-doublefree": {
        "rudra": True,
        "mirchecker": True,
        "ffichecker": True,
    },
    "tests__panic_safety__order_unsafe.rs": {
        "rudra": True,
        "mirchecker": True,
        "ffichecker": None,  # skip
    },
    "cases__panic_double_free": {
        "rudra": True,
        "mirchecker": True,
        "ffichecker": True,
    },
}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run full experiment on all cases with selected tools."
    )
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
        "--skip-known-checks",
        action="store_true",
        help="Skip known-case expectation checks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print planned (case_id, tool) pairs without executing.",
    )
    return parser


def _run_full(cases: list[dict[str, Any]], tools: list[str], raw_dir: Path) -> list[dict]:
    init_failures: dict[str, str] = {}
    runners: dict[str, Any] = {}
    for tool in tools:
        display_name, runner_cls = TOOL_SPECS[tool]
        try:
            runners[tool] = runner_cls()
        except Exception:
            init_failures[tool] = traceback.format_exc()
            print(f"[INIT FAILED] tool={tool} ({display_name})")

    total = len(cases) * len(tools)
    records: list[dict] = []
    index = 0

    for case in cases:
        case_id = str(case["id"])
        case_path = (PROJECT_ROOT / str(case["path"])).resolve()

        for tool in tools:
            index += 1
            print(f"[{index}/{total}] Running tool={tool}, case_id={case_id}")

            if not case_path.exists():
                result = _normalize_result(
                    {
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": f"[full_run] case path not found: {case_path}",
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

    return records


def _print_detected_stats(rows: list[dict[str, str]], tools: list[str]) -> None:
    by_tool: dict[str, dict[str, int]] = {
        tool: {"detected": 0, "total": 0} for tool in tools
    }
    by_scenario: dict[str, dict[str, int]] = {}

    for row in rows:
        tool = str(row.get("tool", "")).strip().lower()
        scenario = str(row.get("scenario", "")).strip() or "(unknown)"
        detected = _parse_bool(row.get("detected"))

        by_tool.setdefault(tool, {"detected": 0, "total": 0})
        by_tool[tool]["total"] += 1
        if detected:
            by_tool[tool]["detected"] += 1

        by_scenario.setdefault(scenario, {"detected": 0, "total": 0})
        by_scenario[scenario]["total"] += 1
        if detected:
            by_scenario[scenario]["detected"] += 1

    print("\nDetected stats by tool:")
    for tool in tools:
        item = by_tool.get(tool, {"detected": 0, "total": 0})
        print(f"- {tool}: detected={item['detected']}/{item['total']}")

    print("\nDetected stats by scenario:")
    for scenario in sorted(by_scenario.keys()):
        item = by_scenario[scenario]
        print(f"- {scenario}: detected={item['detected']}/{item['total']}")


def _validate_known_detections(
    rows: list[dict[str, str]],
    selected_case_ids: set[str],
    selected_tools: set[str],
) -> int:
    row_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        tool = str(row.get("tool", "")).strip().lower()
        if case_id and tool:
            row_map[(case_id, tool)] = row

    mismatch_count = 0
    print("\nKnown-case detection checks:")
    for case_id, expected_by_tool in KNOWN_DETECTION_EXPECTATIONS.items():
        if case_id not in selected_case_ids:
            continue
        for tool, expected in expected_by_tool.items():
            if tool not in selected_tools:
                continue
            if expected is None:
                print(f"- SKIP: case_id={case_id}, tool={tool}")
                continue

            row = row_map.get((case_id, tool))
            if row is None:
                mismatch_count += 1
                print(
                    "WARNING: "
                    f"case_id={case_id}, tool={tool}, expected_detected={expected}, "
                    "actual=missing_row"
                )
                continue

            actual = _parse_bool(row.get("detected"))
            if actual != expected:
                mismatch_count += 1
                print(
                    "WARNING: "
                    f"case_id={case_id}, tool={tool}, expected_detected={expected}, "
                    f"actual_detected={actual}"
                )

    if mismatch_count == 0:
        print("All known-case checks matched expected detected values.")
    else:
        print(f"Known-case mismatches: {mismatch_count}")
    return mismatch_count


def _print_metrics_summary(summary: dict[str, Any]) -> None:
    print("\nMetrics summary (Recall / Executability):")
    tools = [str(t).strip().lower() for t in summary.get("tools", []) if t]
    by_tool = summary.get("by_tool", {})
    if not tools:
        print("- No tool metrics found.")
        return

    for tool in tools:
        item = by_tool.get(tool, {})
        recall = float(item.get("recall", 0.0) or 0.0)
        exec_rate = float(item.get("executability_rate", 0.0) or 0.0)
        print(
            f"- {tool}: recall={recall:.4f}, "
            f"executability={exec_rate:.4f}"
        )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        selected_tools = _parse_tools(args.tools)
    except ValueError as exc:
        parser.error(str(exc))

    if not args.tools:
        selected_tools = [tool for tool in DEFAULT_TOOLS if tool in TOOL_SPECS]
        missing = [tool for tool in DEFAULT_TOOLS if tool not in selected_tools]
        if missing:
            raise RuntimeError(f"Missing tool specs: {', '.join(missing)}")

    all_cases = load_cases()
    try:
        selected_cases = _select_cases(all_cases, args.cases)
    except ValueError as exc:
        parser.error(str(exc))

    total_runs = len(selected_cases) * len(selected_tools)
    print(f"Cases: {len(selected_cases)}")
    print(f"Tools: {len(selected_tools)} ({', '.join(selected_tools)})")
    print(f"Total runs: {total_runs}")

    if args.dry_run:
        print("\nPlanned (case_id, tool) pairs:")
        for case in selected_cases:
            case_id = str(case["id"])
            for tool in selected_tools:
                print(f"({case_id}, {tool})")
        return 0

    results_dir = RESULTS_DIR.resolve()
    raw_dir = (results_dir / "raw").resolve()
    run_log_path = (results_dir / "run_log.csv").resolve()
    normalized_path = (results_dir / "normalized.csv").resolve()
    metrics_summary_path = (results_dir / "metrics_summary.json").resolve()
    metrics_by_scenario_path = (results_dir / "metrics_by_scenario.csv").resolve()
    report_csv_path = (results_dir / "report_table.csv").resolve()
    report_md_path = (results_dir / "report_summary.md").resolve()
    recall_plot_path = (results_dir / "recall_by_scenario.png").resolve()
    exec_plot_path = (results_dir / "executability_by_scenario.png").resolve()

    raw_dir.mkdir(parents=True, exist_ok=True)

    records = _run_full(selected_cases, selected_tools, raw_dir=raw_dir)
    _write_run_log(run_log_path, records)

    normalize(
        run_log_path=run_log_path,
        raw_dir=raw_dir,
        output_path=normalized_path,
    )

    metrics_summary = compute_metrics(
        normalized_path=normalized_path,
        summary_output_path=metrics_summary_path,
        scenario_output_path=metrics_by_scenario_path,
        verbose=False,
    )

    report_result = generate_report(
        normalized_path=normalized_path,
        output_format="both",
        report_csv_path=report_csv_path,
        report_md_path=report_md_path,
        plot=False,
        recall_plot_path=recall_plot_path,
        exec_plot_path=exec_plot_path,
    )

    normalized_rows = _read_csv_rows(normalized_path)
    _print_detected_stats(normalized_rows, selected_tools)
    if not args.skip_known_checks:
        selected_case_ids = {str(case["id"]).strip() for case in selected_cases}
        _validate_known_detections(
            normalized_rows,
            selected_case_ids=selected_case_ids,
            selected_tools=set(selected_tools),
        )
    _print_metrics_summary(metrics_summary)

    report_summary_md = report_result.get("outputs", {}).get(
        "report_summary_md", str(report_md_path)
    )
    print(f"\nreport_summary.md: {report_summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
