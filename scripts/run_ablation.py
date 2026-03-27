#!/usr/bin/env python3
"""Run panic=unwind vs panic=abort ablation experiments on testcase samples."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_ROOT = (REPO_ROOT / "eval").resolve()
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from load_cases import load_cases  # type: ignore  # noqa: E402

SCENARIOS = ("S1", "S2", "S3", "S4")
PANIC_MODES = ("unwind", "abort")

RAW_FIELDS = [
    "run_id",
    "timestamp_utc",
    "seed",
    "sample_size",
    "sample_scope",
    "case_id",
    "scenario",
    "fault_type",
    "selection_order",
    "selection_order_in_scenario",
    "case_path",
    "case_kind",
    "panic_strategy",
    "supported_on_host",
    "executed",
    "success",
    "triggered",
    "panic_detected",
    "memory_error_detected",
    "build_failed",
    "timeout",
    "exit_code",
    "exit_code_hex",
    "termination_signal",
    "termination_kind",
    "duration_sec",
    "log_path",
    "error_reason",
    "platform",
    "python_version",
    "cargo_path",
    "cargo_target",
    "cargo_linker",
]

SUMMARY_FIELDS = [
    "summary_type",
    "group",
    "panic_strategy",
    "records",
    "supported_records",
    "executed_records",
    "success_records",
    "triggered_records",
    "panic_records",
    "memory_error_records",
    "build_failed_records",
    "timeout_records",
    "avg_duration_sec",
]

BUILD_FAILURE_RE = re.compile(
    r"("
    r"could not compile|"
    r"error\[E\d{4}\]|"
    r"linker `.*` not found|"
    r"aborting due to|"
    r"failed to run custom build command|"
    r"failed to get `|"
    r"failed to load source for dependency|"
    r"failed to read `.*Cargo\.toml`|"
    r"error occurred: Command"
    r")",
    re.IGNORECASE,
)
PANIC_RE = re.compile(
    r"(thread '.*' panicked at|panicked at|panic!|stack backtrace)",
    re.IGNORECASE,
)
MEMORY_ERROR_RE = re.compile(
    r"(double free|use after free|heap corruption|access violation|segmentation fault|invalid pointer|STATUS_HEAP_CORRUPTION|STATUS_ACCESS_VIOLATION)",
    re.IGNORECASE,
)
AVAILABLE_BINS_RE = re.compile(r"available binaries?:\s*(.+)", re.IGNORECASE)


def sanitize_name(value: str) -> str:
    safe = (value or "").strip()
    for ch in '<>:"/\\|?*':
        safe = safe.replace(ch, "_")
    return safe.rstrip(" .") or "case"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_cargo() -> str | None:
    home = Path.home()
    default_candidates = [
        home / ".cargo" / "bin" / "cargo.exe",
        home / ".cargo" / "bin" / "cargo",
    ]
    for candidate in (
        os.environ.get("CARGO"),
        shutil.which("cargo"),
        shutil.which("cargo.exe"),
        *(str(path) for path in default_candidates if path.exists()),
    ):
        if candidate:
            return str(Path(candidate).resolve())
    return None


def current_cargo_target() -> str:
    return (os.environ.get("CARGO_BUILD_TARGET") or "").strip()


def current_cargo_linker() -> str:
    target = current_cargo_target()
    if target:
        env_name = f"CARGO_TARGET_{target.upper().replace('-', '_')}_LINKER"
        value = (os.environ.get(env_name) or "").strip()
        if value:
            return value
    return (os.environ.get("RUSTC_LINKER") or "").strip()


def git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=10,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def infer_fault_type(case_id: str) -> str:
    lowered = case_id.lower()
    if "double-free" in lowered or "doublefree" in lowered:
        return "double_free"
    if "use-after-free" in lowered or "uaf" in lowered:
        return "use_after_free"
    if "memleak" in lowered or "leak" in lowered:
        return "memory_leak"
    if "division-by-zero" in lowered:
        return "division_by_zero"
    if "overflow" in lowered:
        return "integer_overflow"
    if "out-of-bound" in lowered or "boundary-check" in lowered or "index" in lowered:
        return "bounds_error"
    if "incorrect-cast" in lowered or "transmute" in lowered:
        return "type_confusion"
    if case_id.startswith("cases__panic_") or case_id.startswith("tests__panic_safety__"):
        return "panic_safety"
    if case_id.startswith("tests__send_sync__"):
        return "send_sync"
    if case_id.startswith("tests__unsafe_destructor__"):
        return "unsafe_destructor"
    if case_id.startswith("tests__safe-bugs__"):
        return "safe_bug"
    if case_id.startswith("tests__unsafe-bugs__"):
        return "unsafe_bug"
    if case_id.startswith("tests__unit-tests__"):
        return "unit_test"
    if case_id.startswith("tests__utility__"):
        return "utility"
    if case_id.startswith("examples__"):
        return "ffi_example"
    if case_id.startswith("trophy-case__"):
        return "trophy_case"
    return "other"


def has_binary_target(case_dir: Path) -> bool:
    manifest = case_dir / "Cargo.toml"
    if not manifest.is_file():
        return False
    if (case_dir / "src" / "main.rs").is_file():
        return True
    text = manifest.read_text(encoding="utf-8", errors="replace")
    return "[[bin]]" in text


def classify_case(case: dict) -> dict:
    case_path = (REPO_ROOT / case["path"]).resolve()
    if case_path.is_file():
        return {
            "case_kind": "rust_fixture",
            "supported_on_host": False,
            "error_reason": "Standalone .rs fixture has no runtime entry point on Windows.",
            "manifest_path": "",
            "working_dir": "",
        }

    if not case_path.is_dir():
        return {
            "case_kind": "missing_path",
            "supported_on_host": False,
            "error_reason": f"Case path not found: {case_path}",
            "manifest_path": "",
            "working_dir": "",
        }

    manifest = case_path / "Cargo.toml"
    if manifest.is_file() and has_binary_target(case_path):
        return {
            "case_kind": "cargo_bin",
            "supported_on_host": True,
            "error_reason": "",
            "manifest_path": str(manifest),
            "working_dir": str(case_path),
        }

    if manifest.is_file():
        return {
            "case_kind": "cargo_non_bin",
            "supported_on_host": False,
            "error_reason": "Cargo project has no runnable binary target for cargo run.",
            "manifest_path": str(manifest),
            "working_dir": str(case_path),
        }

    if (case_path / "Makefile").is_file():
        return {
            "case_kind": "makefile_project",
            "supported_on_host": False,
            "error_reason": "Makefile project is excluded in the Windows MVP runner.",
            "manifest_path": "",
            "working_dir": str(case_path),
        }

    return {
        "case_kind": "directory_no_manifest",
        "supported_on_host": False,
        "error_reason": "Directory case has no Cargo.toml runtime entry.",
        "manifest_path": "",
        "working_dir": "",
    }


def enrich_cases(cases: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for case in cases:
        metadata = classify_case(case)
        enriched_case = dict(case)
        enriched_case.update(metadata)
        enriched_case["fault_type"] = infer_fault_type(case["id"])
        enriched_case["abs_path"] = str((REPO_ROOT / case["path"]).resolve())
        enriched.append(enriched_case)
    return enriched


def allocate_strata(groups: dict[str, list[dict]], sample_size: int) -> dict[str, int]:
    available = {scenario: len(groups.get(scenario, [])) for scenario in SCENARIOS}
    total_available = sum(available.values())
    if total_available == 0:
        raise ValueError("No cases available for sampling.")

    target = min(sample_size, total_available)
    quotas = {scenario: 0 for scenario in SCENARIOS}
    remainders: list[tuple[float, int, str]] = []

    for scenario in SCENARIOS:
        size = available[scenario]
        if size == 0:
            continue
        exact = target * size / total_available
        base = int(exact)
        quotas[scenario] = min(base, size)
        remainders.append((exact - base, size, scenario))

    remaining = target - sum(quotas.values())
    for _, _, scenario in sorted(remainders, reverse=True):
        if remaining <= 0:
            break
        if quotas[scenario] >= available[scenario]:
            continue
        quotas[scenario] += 1
        remaining -= 1

    nonempty = [scenario for scenario in SCENARIOS if available[scenario] > 0]
    if target >= len(nonempty):
        for scenario in nonempty:
            if quotas[scenario] > 0:
                continue
            donors = [
                donor
                for donor in nonempty
                if quotas[donor] > 1 and quotas[donor] <= available[donor]
            ]
            if not donors:
                continue
            donor = max(donors, key=lambda item: (quotas[item], available[item], item))
            quotas[donor] -= 1
            quotas[scenario] += 1

    return quotas


def pick_sample(
    cases: list[dict],
    sample_size: int,
    seed: int,
    sample_scope: str,
) -> tuple[list[dict], dict[str, int]]:
    if sample_scope == "runnable":
        pool = [case for case in cases if case["supported_on_host"]]
    else:
        pool = list(cases)

    if not pool:
        raise ValueError(f"No cases available for sample_scope={sample_scope!r}.")

    groups: dict[str, list[dict]] = {scenario: [] for scenario in SCENARIOS}
    for case in pool:
        groups[case["scenario"]].append(case)

    quotas = allocate_strata(groups, sample_size)
    rng = random.Random(seed)

    selected: list[dict] = []
    order = 0
    for scenario in SCENARIOS:
        candidates = sorted(groups[scenario], key=lambda item: item["id"])
        rng.shuffle(candidates)
        picked = candidates[: quotas[scenario]]
        for idx, case in enumerate(picked, start=1):
            order += 1
            selected_case = dict(case)
            selected_case["selection_order"] = order
            selected_case["selection_order_in_scenario"] = idx
            selected.append(selected_case)

    return selected, quotas


def resolve_case_ids(cases: list[dict], raw_ids: str) -> list[dict]:
    wanted = [item.strip() for item in raw_ids.split(",") if item.strip()]
    if not wanted:
        raise ValueError("--case-ids cannot be empty.")

    case_by_id = {case["id"]: case for case in cases}
    missing = [case_id for case_id in wanted if case_id not in case_by_id]
    if missing:
        raise ValueError(f"Unknown case IDs: {', '.join(missing)}")

    selected: list[dict] = []
    for order, case_id in enumerate(wanted, start=1):
        case = dict(case_by_id[case_id])
        case["selection_order"] = order
        case["selection_order_in_scenario"] = 1
        selected.append(case)
    return selected


def build_run_command(
    cargo_path: str,
    manifest_path: str,
    target_dir: Path,
    bin_name: str | None = None,
) -> list[str]:
    cmd = [
        cargo_path,
        "run",
        "--quiet",
        "--color",
        "never",
        "--manifest-path",
        manifest_path,
        "--target-dir",
        str(target_dir),
    ]
    if bin_name:
        cmd.extend(["--bin", bin_name])
    return cmd


def detect_available_bin(stderr: str) -> str | None:
    match = AVAILABLE_BINS_RE.search(stderr or "")
    if not match:
        return None
    values = [item.strip(" .'\"") for item in match.group(1).split(",") if item.strip()]
    return values[0] if values else None


def run_command(
    cmd: list[str],
    cwd: str,
    env: dict[str, str],
    timeout_sec: float,
) -> dict:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - started
        return {
            "success": False,
            "timeout": True,
            "exit_code": -1,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\n[ablation] timed out after {timeout_sec:.1f}s",
            "duration_sec": round(duration, 6),
        }
    except OSError as exc:
        duration = time.perf_counter() - started
        return {
            "success": False,
            "timeout": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"[ablation] failed to execute command: {exc}",
            "duration_sec": round(duration, 6),
        }

    duration = time.perf_counter() - started
    return {
        "success": completed.returncode == 0,
        "timeout": False,
        "exit_code": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "duration_sec": round(duration, 6),
    }


def exit_code_hex(value: int) -> str:
    return f"0x{(int(value) & 0xFFFFFFFF):08X}"


def detect_memory_error(text: str, exit_hex: str) -> bool:
    return bool(MEMORY_ERROR_RE.search(text) or exit_hex in {"0xC0000005", "0xC0000374"})


def classify_termination(
    *,
    supported_on_host: bool,
    timeout: bool,
    build_failed: bool,
    exit_code: int,
    exit_hex: str,
    panic_detected: bool,
    memory_error_detected: bool,
) -> str:
    if not supported_on_host:
        return "unsupported"
    if timeout:
        return "timeout"
    if build_failed:
        return "build_failed"
    if memory_error_detected:
        if exit_hex == "0xC0000005":
            return "access_violation"
        if exit_hex == "0xC0000374":
            return "heap_corruption"
        return "memory_error"
    if panic_detected:
        if exit_code == 101:
            return "panic_unwind"
        if exit_code != 0:
            return "panic_abort"
        return "panic_caught"
    if exit_code == 0:
        return "success"
    if exit_hex == "0xC0000409":
        return "abort"
    return "nonzero_exit"


def make_env(panic_strategy: str) -> dict[str, str]:
    env = os.environ.copy()
    extra_flag = f"-C panic={panic_strategy}"
    existing = (env.get("RUSTFLAGS") or "").strip()
    env["RUSTFLAGS"] = f"{existing} {extra_flag}".strip()
    env["CARGO_TERM_COLOR"] = "never"
    env["RUST_BACKTRACE"] = "1"
    return env


def write_log(log_path: Path, record: dict, stdout: str, stderr: str, command: list[str] | None) -> None:
    lines = [
        f"run_id: {record['run_id']}",
        f"timestamp_utc: {record['timestamp_utc']}",
        f"case_id: {record['case_id']}",
        f"scenario: {record['scenario']}",
        f"fault_type: {record['fault_type']}",
        f"panic_strategy: {record['panic_strategy']}",
        f"case_kind: {record['case_kind']}",
        f"supported_on_host: {record['supported_on_host']}",
        f"executed: {record['executed']}",
        f"success: {record['success']}",
        f"triggered: {record['triggered']}",
        f"panic_detected: {record['panic_detected']}",
        f"memory_error_detected: {record['memory_error_detected']}",
        f"build_failed: {record['build_failed']}",
        f"timeout: {record['timeout']}",
        f"exit_code: {record['exit_code']}",
        f"exit_code_hex: {record['exit_code_hex']}",
        f"termination_kind: {record['termination_kind']}",
        f"duration_sec: {record['duration_sec']}",
        f"error_reason: {record['error_reason']}",
        f"command: {' '.join(command) if command else ''}",
        "",
        "===== STDOUT =====",
        stdout or "",
        "",
        "===== STDERR =====",
        stderr or "",
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines), encoding="utf-8")


def execute_case(
    case: dict,
    panic_strategy: str,
    seed: int,
    sample_size: int,
    sample_scope: str,
    cargo_path: str | None,
    timeout_sec: float,
    output_dir: Path,
    run_timestamp: str,
    platform_text: str,
) -> dict:
    run_id = f"{sanitize_name(case['id'])}_{panic_strategy}"
    log_dir = output_dir / "ablation_logs"
    build_dir = output_dir / "ablation_artifacts" / "build" / sanitize_name(case["id"]) / panic_strategy
    log_path = log_dir / f"{run_id}.log"

    record = {
        "run_id": run_id,
        "timestamp_utc": run_timestamp,
        "seed": seed,
        "sample_size": sample_size,
        "sample_scope": sample_scope,
        "case_id": case["id"],
        "scenario": case["scenario"],
        "fault_type": case["fault_type"],
        "selection_order": case["selection_order"],
        "selection_order_in_scenario": case["selection_order_in_scenario"],
        "case_path": case["path"],
        "case_kind": case["case_kind"],
        "panic_strategy": panic_strategy,
        "supported_on_host": bool(case["supported_on_host"]),
        "executed": False,
        "success": False,
        "triggered": False,
        "panic_detected": False,
        "memory_error_detected": False,
        "build_failed": False,
        "timeout": False,
        "exit_code": -1,
        "exit_code_hex": exit_code_hex(-1),
        "termination_signal": "",
        "termination_kind": "unsupported",
        "duration_sec": 0.0,
        "log_path": str(log_path.resolve()),
        "error_reason": case["error_reason"],
        "platform": platform_text,
        "python_version": platform.python_version(),
        "cargo_path": cargo_path or "",
        "cargo_target": current_cargo_target(),
        "cargo_linker": current_cargo_linker(),
    }

    command: list[str] | None = None
    stdout = ""
    stderr = ""

    if not case["supported_on_host"]:
        write_log(log_path, record, stdout, stderr, command)
        return record

    if not cargo_path:
        record["supported_on_host"] = False
        record["termination_kind"] = "unsupported"
        record["error_reason"] = "cargo executable not found in PATH or CARGO env var."
        write_log(log_path, record, stdout, stderr, command)
        return record

    command = build_run_command(
        cargo_path=cargo_path,
        manifest_path=case["manifest_path"],
        target_dir=build_dir,
    )
    result = run_command(
        cmd=command,
        cwd=case["working_dir"],
        env=make_env(panic_strategy),
        timeout_sec=timeout_sec,
    )

    if (
        not result["timeout"]
        and result["exit_code"] != 0
        and "a bin target must be available" in result["stderr"].lower()
    ):
        bin_name = detect_available_bin(result["stderr"])
        if bin_name:
            command = build_run_command(
                cargo_path=cargo_path,
                manifest_path=case["manifest_path"],
                target_dir=build_dir,
                bin_name=bin_name,
            )
            result = run_command(
                cmd=command,
                cwd=case["working_dir"],
                env=make_env(panic_strategy),
                timeout_sec=timeout_sec,
            )

    stdout = result["stdout"]
    stderr = result["stderr"]
    combined = f"{stdout}\n{stderr}"
    build_failed = bool(BUILD_FAILURE_RE.search(combined))
    exit_hex = exit_code_hex(result["exit_code"])
    panic_detected = bool(PANIC_RE.search(combined))
    memory_error = detect_memory_error(combined, exit_hex)
    termination_kind = classify_termination(
        supported_on_host=True,
        timeout=result["timeout"],
        build_failed=build_failed,
        exit_code=result["exit_code"],
        exit_hex=exit_hex,
        panic_detected=panic_detected,
        memory_error_detected=memory_error,
    )
    triggered = (
        not build_failed
        and not result["timeout"]
        and (
            panic_detected
            or memory_error
            or (result["exit_code"] != 0 and termination_kind not in {"unsupported", "build_failed"})
        )
    )

    record.update(
        {
            "executed": True,
            "success": bool(result["success"]),
            "triggered": bool(triggered),
            "panic_detected": bool(panic_detected),
            "memory_error_detected": bool(memory_error),
            "build_failed": bool(build_failed),
            "timeout": bool(result["timeout"]),
            "exit_code": int(result["exit_code"]),
            "exit_code_hex": exit_hex,
            "termination_kind": termination_kind,
            "duration_sec": float(result["duration_sec"]),
            "error_reason": "" if result["success"] else (case["error_reason"] or termination_kind),
        }
    )
    if build_failed and not record["error_reason"]:
        record["error_reason"] = "Cargo build failed under the selected panic strategy."

    write_log(log_path, record, stdout, stderr, command)
    return record


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def make_summary(records: list[dict]) -> list[dict]:
    summary_rows: list[dict] = []
    group_specs: list[tuple[str, str, str]] = [("overall", "ALL", "ALL")]
    group_specs.extend(("scenario", scenario, scenario) for scenario in SCENARIOS)
    for fault_type in sorted({record["fault_type"] for record in records}):
        group_specs.append(("fault_type", fault_type, fault_type))

    for summary_type, group_label, group_value in group_specs:
        for panic_strategy in PANIC_MODES:
            subset = [
                record
                for record in records
                if record["panic_strategy"] == panic_strategy
                and (summary_type == "overall" or record[summary_type] == group_value)
            ]
            if not subset:
                continue

            durations = [float(record["duration_sec"]) for record in subset if record["executed"]]
            summary_rows.append(
                {
                    "summary_type": summary_type,
                    "group": group_label,
                    "panic_strategy": panic_strategy,
                    "records": len(subset),
                    "supported_records": sum(1 for record in subset if record["supported_on_host"]),
                    "executed_records": sum(1 for record in subset if record["executed"]),
                    "success_records": sum(1 for record in subset if record["success"]),
                    "triggered_records": sum(1 for record in subset if record["triggered"]),
                    "panic_records": sum(1 for record in subset if record["panic_detected"]),
                    "memory_error_records": sum(1 for record in subset if record["memory_error_detected"]),
                    "build_failed_records": sum(1 for record in subset if record["build_failed"]),
                    "timeout_records": sum(1 for record in subset if record["timeout"]),
                    "avg_duration_sec": round(sum(durations) / len(durations), 6) if durations else 0.0,
                }
            )
    return summary_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run panic=unwind vs panic=abort ablation experiments."
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified sampling.")
    parser.add_argument("--n", type=int, default=20, help="Number of cases to sample.")
    parser.add_argument(
        "--sample-scope",
        choices=("all", "runnable"),
        default="all",
        help="Sample from all 100 cases or only from runnable Cargo binary cases.",
    )
    parser.add_argument(
        "--case-ids",
        help="Comma-separated case IDs. When provided, skip random sampling and run these cases directly.",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=300.0,
        help="Per-case timeout in seconds.",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory for ablation outputs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the selected sample without executing cargo.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.n <= 0:
        parser.error("--n must be > 0.")
    if args.timeout_sec <= 0:
        parser.error("--timeout-sec must be > 0.")

    cases = enrich_cases(load_cases())
    output_dir = (REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.case_ids:
        selected = resolve_case_ids(cases, args.case_ids)
        quotas = {scenario: 0 for scenario in SCENARIOS}
        for case in selected:
            quotas[case["scenario"]] += 1
        sample_size = len(selected)
    else:
        selected, quotas = pick_sample(
            cases=cases,
            sample_size=args.n,
            seed=args.seed,
            sample_scope=args.sample_scope,
        )
        sample_size = len(selected)

    selection_payload = {
        "timestamp_utc": utc_now(),
        "seed": args.seed,
        "requested_n": args.n,
        "actual_n": sample_size,
        "sample_scope": args.sample_scope,
        "quotas": quotas,
        "selected_cases": [
            {
                "case_id": case["id"],
                "scenario": case["scenario"],
                "fault_type": case["fault_type"],
                "case_kind": case["case_kind"],
                "supported_on_host": case["supported_on_host"],
                "case_path": case["path"],
                "selection_order": case["selection_order"],
            }
            for case in selected
        ],
    }
    write_json(output_dir / "ablation_selection.json", selection_payload)

    if args.dry_run:
        print(f"Selected {sample_size} cases with seed={args.seed} sample_scope={args.sample_scope}")
        for case in selected:
            print(
                f"[{case['selection_order']:02d}] {case['scenario']} {case['id']} "
                f"kind={case['case_kind']} supported={case['supported_on_host']}"
            )
        print(f"Selection file: {(output_dir / 'ablation_selection.json').resolve()}")
        return 0

    run_timestamp = utc_now()
    platform_text = platform.platform()
    cargo_path = find_cargo()
    records: list[dict] = []

    for case in selected:
        for panic_strategy in PANIC_MODES:
            record = execute_case(
                case=case,
                panic_strategy=panic_strategy,
                seed=args.seed,
                sample_size=sample_size,
                sample_scope=args.sample_scope,
                cargo_path=cargo_path,
                timeout_sec=args.timeout_sec,
                output_dir=output_dir,
                run_timestamp=run_timestamp,
                platform_text=platform_text,
            )
            records.append(record)
            print(
                f"[{record['selection_order']:02d}/{sample_size:02d}] "
                f"{record['case_id']} panic={panic_strategy} "
                f"kind={record['termination_kind']} exit={record['exit_code_hex']}"
            )

    summary_rows = make_summary(records)
    metadata = {
        "timestamp_utc": run_timestamp,
        "seed": args.seed,
        "sample_size": sample_size,
        "sample_scope": args.sample_scope,
        "platform": {
            "platform": platform_text,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "cargo_path": cargo_path or "",
        "cargo_target": current_cargo_target(),
        "cargo_linker": current_cargo_linker(),
        "git_commit": git_commit() or "",
        "quotas": quotas,
        "counts": {
            "loaded_cases": len(cases),
            "selected_cases": sample_size,
            "records": len(records),
            "supported_records": sum(1 for record in records if record["supported_on_host"]),
            "executed_records": sum(1 for record in records if record["executed"]),
            "triggered_records": sum(1 for record in records if record["triggered"]),
            "memory_error_records": sum(1 for record in records if record["memory_error_detected"]),
            "build_failed_records": sum(1 for record in records if record["build_failed"]),
            "timeout_records": sum(1 for record in records if record["timeout"]),
        },
    }

    write_csv(output_dir / "ablation_raw.csv", RAW_FIELDS, records)
    write_json(output_dir / "ablation_raw.json", records)
    write_csv(output_dir / "ablation_summary.csv", SUMMARY_FIELDS, summary_rows)
    write_json(output_dir / "ablation_summary.json", summary_rows)
    write_json(output_dir / "ablation_run_metadata.json", metadata)

    print(f"Raw CSV: {(output_dir / 'ablation_raw.csv').resolve()}")
    print(f"Summary CSV: {(output_dir / 'ablation_summary.csv').resolve()}")
    print(f"Metadata JSON: {(output_dir / 'ablation_run_metadata.json').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
