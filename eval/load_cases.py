"""Load testcase metadata from testcase_categories.csv."""

from __future__ import annotations

import csv
import sys
from collections import Counter

try:
    from .config import CSV_PATH, PROJECT_ROOT, TESTCASES_ROOT
except ImportError:
    from config import CSV_PATH, PROJECT_ROOT, TESTCASES_ROOT

VALID_SCENARIOS = {"S1", "S2", "S3", "S4"}


def _warn(message: str) -> None:
    print(f"[load_cases] WARNING: {message}", file=sys.stderr)


def _is_valid_case_name(case_name: str) -> bool:
    if not case_name:
        return False
    if case_name.endswith("README.md"):
        return False
    if case_name.endswith("__"):
        return False
    return True


def load_cases() -> list[dict]:
    """Return testcase list with id/scenario/path loaded from CSV."""
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        raise ValueError(f"CSV must contain at least 2 rows: {CSV_PATH}")

    case_names = [cell.strip() for cell in rows[0][1:]]
    scenarios = [cell.strip() for cell in rows[1][1:]]

    if len(case_names) != len(scenarios):
        _warn(
            "Header/scenario column count mismatch: "
            f"{len(case_names)} vs {len(scenarios)}. Using the shortest length."
        )

    cases: list[dict] = []
    for case_name, scenario in zip(case_names, scenarios):
        if not _is_valid_case_name(case_name):
            _warn(f"Skipping invalid case name: {case_name!r}")
            continue

        if scenario not in VALID_SCENARIOS:
            _warn(f"Skipping {case_name!r}: invalid scenario {scenario!r}")
            continue

        candidate = TESTCASES_ROOT / case_name
        if candidate.is_dir() or candidate.is_file():
            rel_path = candidate.resolve().relative_to(PROJECT_ROOT).as_posix()
            cases.append({"id": case_name, "scenario": scenario, "path": rel_path})
            continue

        _warn(f"Skipping {case_name!r}: path not found ({candidate})")

    return cases


if __name__ == "__main__":
    loaded_cases = load_cases()
    print(f"Loaded cases: {len(loaded_cases)}")

    counts = Counter(case["scenario"] for case in loaded_cases)
    for scenario in ("S1", "S2", "S3", "S4"):
        print(f"{scenario}: {counts.get(scenario, 0)}")
