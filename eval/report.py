"""Generate summary reports from normalized metrics."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import RESULTS_DIR
    from metrics import SCENARIO_ORDER, compute_metrics
except ImportError:
    from .config import RESULTS_DIR
    from .metrics import SCENARIO_ORDER, compute_metrics

DEFAULT_REPORT_CSV = (RESULTS_DIR / "report_table.csv").resolve()
DEFAULT_REPORT_MD = (RESULTS_DIR / "report_summary.md").resolve()
DEFAULT_RECALL_PLOT = (RESULTS_DIR / "recall_by_scenario.png").resolve()
DEFAULT_EXEC_PLOT = (RESULTS_DIR / "executability_by_scenario.png").resolve()


def _parse_float(value: Any) -> float:
    try:
        return float(str(value or "0").strip())
    except (TypeError, ValueError):
        return 0.0


def _scenario_sort_key(scenario: str) -> tuple[int, str]:
    if scenario in SCENARIO_ORDER:
        return (SCENARIO_ORDER.index(scenario), scenario)
    return (len(SCENARIO_ORDER), scenario)


def _read_duration_records(
    normalized_path: Path,
    valid_tools: set[str],
    valid_scenarios: set[str],
) -> dict[tuple[str, str], list[float]]:
    latest_by_tool_case: dict[tuple[str, str], tuple[str, float]] = {}
    with normalized_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            case_id = str(row.get("case_id", "")).strip()
            tool = str(row.get("tool", "")).strip().lower()
            scenario = str(row.get("scenario", "")).strip()
            if not case_id or not tool:
                continue
            if tool not in valid_tools or scenario not in valid_scenarios:
                continue
            duration = _parse_float(row.get("duration_sec", row.get("duration")))
            latest_by_tool_case[(tool, case_id)] = (scenario, duration)

    durations: dict[tuple[str, str], list[float]] = {}
    for (tool, _), (scenario, duration) in latest_by_tool_case.items():
        durations.setdefault((tool, scenario), []).append(duration)
    return durations


def _build_report_rows(
    summary: dict[str, Any],
    durations: dict[tuple[str, str], list[float]],
) -> list[dict[str, Any]]:
    by_tool_scenario = summary.get("by_tool_scenario", {})
    tools = [str(tool).strip().lower() for tool in summary.get("tools", []) if tool]
    scenarios = sorted(summary.get("cases_by_scenario", {}).keys(), key=_scenario_sort_key)

    rows: list[dict[str, Any]] = []
    for tool in tools:
        tool_bucket = by_tool_scenario.get(tool, {})
        for scenario in scenarios:
            cell = tool_bucket.get(scenario, {})
            observed_durations = durations.get((tool, scenario), [])
            avg_duration = (
                sum(observed_durations) / len(observed_durations)
                if observed_durations
                else 0.0
            )
            rows.append(
                {
                    "tool": tool,
                    "scenario": scenario,
                    "recall": _parse_float(cell.get("recall")),
                    "executability_rate": _parse_float(cell.get("executability_rate")),
                    "avg_duration_sec": avg_duration,
                }
            )
    return rows


def _write_report_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "tool",
        "scenario",
        "recall",
        "executability_rate",
        "avg_duration_sec",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "tool": row["tool"],
                    "scenario": row["scenario"],
                    "recall": f"{row['recall']:.6f}",
                    "executability_rate": f"{row['executability_rate']:.6f}",
                    "avg_duration_sec": f"{row['avg_duration_sec']:.6f}",
                }
            )


def _write_report_md(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evaluation Report Summary",
        "",
        f"- Generated at (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Tool | Scenario | Recall | Executability | Avg Time (s) |",
        "| --- | --- | ---: | ---: | ---: |",
    ]

    if not rows:
        lines.append("| - | - | - | - | - |")
    else:
        for row in rows:
            lines.append(
                "| "
                f"{row['tool']} | "
                f"{row['scenario']} | "
                f"{row['recall']:.2%} | "
                f"{row['executability_rate']:.2%} | "
                f"{row['avg_duration_sec']:.6f} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_grouped_bar_chart(
    rows: list[dict[str, Any]],
    metric_key: str,
    y_label: str,
    title: str,
    output_path: Path,
) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"[report] Skip plot {output_path.name}: matplotlib unavailable ({exc})")
        return False

    if not rows:
        print(f"[report] Skip plot {output_path.name}: no data rows.")
        return False

    tools = list(dict.fromkeys(str(row["tool"]) for row in rows))
    scenario_set = {str(row["scenario"]) for row in rows}
    scenarios = sorted(scenario_set, key=_scenario_sort_key)
    if not tools or not scenarios:
        print(f"[report] Skip plot {output_path.name}: no tools/scenarios.")
        return False

    values = {
        (str(row["tool"]), str(row["scenario"])): _parse_float(row.get(metric_key))
        for row in rows
    }
    x_positions = list(range(len(scenarios)))
    width = 0.8 / max(len(tools), 1)

    fig_width = max(7.0, len(scenarios) * 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, 4.8))
    for idx, tool in enumerate(tools):
        offset = -0.4 + (width / 2.0) + (idx * width)
        bar_positions = [x + offset for x in x_positions]
        bar_values = [values.get((tool, scenario), 0.0) for scenario in scenarios]
        ax.bar(bar_positions, bar_values, width=width, label=tool)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.set_xlabel("Scenario")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return True


def generate_report(
    normalized_path: Path,
    output_format: str,
    report_csv_path: Path,
    report_md_path: Path,
    plot: bool,
    recall_plot_path: Path,
    exec_plot_path: Path,
) -> dict[str, Any]:
    summary = compute_metrics(normalized_path=normalized_path, verbose=False)
    tools = {str(tool).strip().lower() for tool in summary.get("tools", []) if tool}
    scenarios = {
        str(scenario).strip()
        for scenario in summary.get("cases_by_scenario", {}).keys()
        if scenario
    }
    durations = _read_duration_records(
        normalized_path,
        valid_tools=tools,
        valid_scenarios=scenarios,
    )
    rows = _build_report_rows(summary, durations=durations)

    outputs: dict[str, str] = {}
    if output_format in {"csv", "both"}:
        _write_report_csv(report_csv_path, rows)
        outputs["report_table_csv"] = str(report_csv_path)
    if output_format in {"md", "both"}:
        _write_report_md(report_md_path, rows)
        outputs["report_summary_md"] = str(report_md_path)

    if plot:
        if _write_grouped_bar_chart(
            rows=rows,
            metric_key="recall",
            y_label="Recall",
            title="Recall by Scenario",
            output_path=recall_plot_path,
        ):
            outputs["recall_plot_png"] = str(recall_plot_path)
        if _write_grouped_bar_chart(
            rows=rows,
            metric_key="executability_rate",
            y_label="Executability Rate",
            title="Executability by Scenario",
            output_path=exec_plot_path,
        ):
            outputs["executability_plot_png"] = str(exec_plot_path)

    return {
        "rows": rows,
        "outputs": outputs,
        "summary": summary,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate report table and markdown summary.")
    parser.add_argument(
        "--normalized",
        default=str((RESULTS_DIR / "normalized.csv").resolve()),
        help="Path to normalized.csv",
    )
    parser.add_argument(
        "--format",
        choices=("md", "csv", "both"),
        default="both",
        help="Output format for the report files.",
    )
    parser.add_argument(
        "--report-csv",
        default=str(DEFAULT_REPORT_CSV),
        help="Path to report_table.csv",
    )
    parser.add_argument(
        "--report-md",
        default=str(DEFAULT_REPORT_MD),
        help="Path to report_summary.md",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate scenario bar charts with matplotlib.",
    )
    parser.add_argument(
        "--recall-plot",
        default=str(DEFAULT_RECALL_PLOT),
        help="Path to recall_by_scenario.png",
    )
    parser.add_argument(
        "--executability-plot",
        default=str(DEFAULT_EXEC_PLOT),
        help="Path to executability_by_scenario.png",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    result = generate_report(
        normalized_path=Path(args.normalized).resolve(),
        output_format=args.format,
        report_csv_path=Path(args.report_csv).resolve(),
        report_md_path=Path(args.report_md).resolve(),
        plot=bool(args.plot),
        recall_plot_path=Path(args.recall_plot).resolve(),
        exec_plot_path=Path(args.executability_plot).resolve(),
    )

    print(f"Report rows: {len(result['rows'])}")
    if not result["outputs"]:
        print("No output files were generated.")
        return 0

    print("Generated files:")
    for _, output_path in result["outputs"].items():
        print(f"- {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
