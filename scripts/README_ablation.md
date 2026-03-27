# Panic Ablation Runner

This script automates an MVP ablation for comparing `panic=unwind` and `panic=abort` on the testcase set in this repository.

## Entry Command

```powershell
python scripts/run_ablation.py --seed 42 --n 20
```

Useful variants:

```powershell
python scripts/run_ablation.py --seed 42 --n 20 --sample-scope runnable
python scripts/run_ablation.py --case-ids cases__panic_double_free,cases__panic_safe_guard
python scripts/run_ablation.py --seed 42 --n 20 --dry-run
```

## What It Does

1. Loads the 100 cases from `testcases/testcase_categories.csv`.
2. Performs reproducible stratified sampling over `S1` to `S4`.
3. Runs each sampled case twice with:
   - `RUSTFLAGS=-C panic=unwind`
   - `RUSTFLAGS=-C panic=abort`
4. Captures exit behavior, panic markers, memory-error markers, duration, and per-run logs.
5. Writes raw and summary tables for plotting and thesis statistics.

## Output Files

Default output directory: `results/`

- `results/ablation_raw.csv`: one row per `(case, panic_strategy)`.
- `results/ablation_raw.json`: JSON version of the raw records.
- `results/ablation_summary.csv`: aggregated rows by scenario, fault type, and overall.
- `results/ablation_summary.json`: JSON version of the summary.
- `results/ablation_run_metadata.json`: seed, platform, git commit, and run-level counts.
- `results/ablation_selection.json`: sampled case list and stratum quotas.
- `results/ablation_logs/*.log`: raw stdout/stderr for each run.

Key raw columns:

- `case_id`, `scenario`, `fault_type`
- `panic_strategy`
- `triggered`
- `exit_code`, `exit_code_hex`
- `termination_kind`
- `panic_detected`
- `memory_error_detected`
- `build_failed`, `timeout`
- `log_path`

## Windows MVP Scope

The current MVP runner is intentionally conservative:

- Supported: Cargo binary projects that can be executed with `cargo run`.
- Recorded as unsupported: standalone `.rs` fixtures, Cargo library-only projects, and Makefile-only cases.
- The script never edits `Cargo.toml`; panic mode is switched through `RUSTFLAGS` and separate build directories.
- A single failing case does not stop the batch.

This matters in this repository because the 100-case pool mixes runtime projects and analysis-only fixtures. If you want a fully executable 20-case batch on Windows, use:

```powershell
python scripts/run_ablation.py --seed 42 --n 20 --sample-scope runnable
```

## Prerequisites

- Python 3
- Rust toolchain with `cargo` available in `PATH`, or set `CARGO` explicitly

If `cargo` is missing, the script still completes and records the runs as unsupported instead of crashing.

## Thesis Methods Snippet

We implemented a lightweight ablation runner to compare runtime behavior under `panic=unwind` and `panic=abort`. The runner loads the repository testcase inventory, performs seed-controlled stratified sampling across the four scenario strata (`S1-S4`), and executes each sampled case under two panic configurations using temporary `RUSTFLAGS` rather than persistent manifest edits. For each run, we record exit status, panic signals, memory-error indicators, elapsed time, platform metadata, and the raw execution log. The MVP design prioritizes reproducibility and fault tolerance: unsupported or failed cases are logged and skipped without interrupting the remaining batch.
