"""Evaluation configuration for RustSec experiment runners."""

from pathlib import Path

# Project root = .../paper_rustSec
PROJECT_ROOT = Path(__file__).resolve().parent.parent

TESTCASES_ROOT = (PROJECT_ROOT / "testcases").resolve()
TOOLS_ROOT = (PROJECT_ROOT / "tools").resolve()
CSV_PATH = (TESTCASES_ROOT / "testcase_categories.csv").resolve()
RESULTS_DIR = (PROJECT_ROOT / "eval" / "results").resolve()

# Rudra on FFI testcases requires a pre-run `cargo build` (including C compilation).
# This compile phase often exceeds 10 minutes, so timeout is set to 20 minutes.
TIMEOUT_SECONDS = 1200
