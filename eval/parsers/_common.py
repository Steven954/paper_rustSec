"""Shared helpers for parsing analyzer stdout/stderr outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
KEYWORD_RE = re.compile(
    r"(?i)\b(?:error|warning|warn|bug|unsafe|panic|vulnerability|fatal)\b"
)
FILE_LINE_RE = re.compile(
    r"(?P<file>(?:[A-Za-z]:)?[^\s:]+(?:[\\/][^\s:]+)*\.[A-Za-z0-9_]+):(?P<line>\d+)(?::\d+)?"
)
LINE_NUMBER_RE = re.compile(r"(?i)\bline\s+(?P<line>\d+)\b")
FILE_LINE_MESSAGE_RE = re.compile(
    r"^\s*(?P<file>(?:[A-Za-z]:)?[^\s:]+(?:[\\/][^\s:]+)*\.[A-Za-z0-9_]+):"
    r"(?P<line>\d+)(?::\d+)?\s*:\s*(?P<message>.+?)\s*$"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI control sequences."""
    return ANSI_ESCAPE_RE.sub("", text or "")


def normalize_message(text: str) -> str:
    """Normalize whitespace in diagnostic messages."""
    return re.sub(r"\s+", " ", text or "").strip()


def has_alert_keywords(*texts: str) -> bool:
    """Whether any alert-like keyword appears."""
    merged = "\n".join(value for value in texts if value)
    return bool(KEYWORD_RE.search(merged))


def extract_location(text: str) -> tuple[str, int] | None:
    """Extract first file:line (or fallback line N) location from text."""
    match = FILE_LINE_RE.search(text or "")
    if match:
        file_path = match.group("file") or ""
        line_no = int(match.group("line"))
        return (file_path, line_no)

    line_match = LINE_NUMBER_RE.search(text or "")
    if line_match:
        return ("", int(line_match.group("line")))
    return None


def parse_file_line_message(line: str) -> tuple[str, int, str] | None:
    """Parse lines in 'path:line[:col]: message' format."""
    match = FILE_LINE_MESSAGE_RE.match(line or "")
    if not match:
        return None
    file_path = match.group("file") or ""
    line_no = int(match.group("line"))
    message = normalize_message(match.group("message") or "")
    return (file_path, line_no, message)


def make_alert(
    file_path: str,
    line: int,
    message: str,
    rule_id: str | None = None,
) -> dict[str, Any]:
    """Build one normalized alert record."""
    normalized_line = int(line) if line and int(line) > 0 else 0
    normalized_rule = (rule_id or "").strip() or None
    return {
        "file": file_path or "",
        "line": normalized_line,
        "message": normalize_message(message),
        "rule_id": normalized_rule,
    }


def dedupe_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve order while removing duplicate alerts."""
    seen: set[tuple[str, int, str, str | None]] = set()
    unique: list[dict[str, Any]] = []
    for alert in alerts:
        key = (
            str(alert.get("file", "")),
            int(alert.get("line", 0) or 0),
            str(alert.get("message", "")),
            alert.get("rule_id"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(
            make_alert(
                file_path=key[0],
                line=key[1],
                message=key[2],
                rule_id=key[3],
            )
        )
    return unique


def split_raw_result(content: str) -> tuple[str, str]:
    """Split run_experiment raw bundle into stdout/stderr sections."""
    text = content or ""
    stdout_marker = "===== STDOUT ====="
    stderr_marker = "===== STDERR ====="
    if stdout_marker in text and stderr_marker in text:
        after_stdout = text.split(stdout_marker, 1)[1]
        stdout_text, stderr_text = after_stdout.split(stderr_marker, 1)
        return (stdout_text.strip(), stderr_text.strip())
    return (text.strip(), "")


def load_tool_samples(
    tool_key: str,
    inspect_prefix: str,
    limit: int = 5,
) -> list[tuple[str, str, str]]:
    """Load sample outputs from results/raw (fallback: results/inspect)."""
    results_dir = Path(__file__).resolve().parents[1] / "results"
    samples: list[tuple[str, str, str]] = []

    raw_dir = results_dir / "raw"
    if raw_dir.is_dir():
        raw_files = sorted(raw_dir.glob(f"{tool_key}_*.txt"))
        for path in raw_files:
            content = path.read_text(encoding="utf-8", errors="replace")
            stdout_text, stderr_text = split_raw_result(content)
            samples.append((path.name, stdout_text, stderr_text))
            if len(samples) >= limit:
                return samples

    inspect_dir = results_dir / "inspect"
    if inspect_dir.is_dir():
        stdout_files = sorted(inspect_dir.glob(f"{inspect_prefix}_*_stdout.txt"))
        for stdout_path in stdout_files:
            stderr_name = stdout_path.name.replace("_stdout.txt", "_stderr.txt")
            stderr_path = stdout_path.with_name(stderr_name)
            stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
            if stderr_path.is_file():
                stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
            else:
                stderr_text = ""
            samples.append((stdout_path.name, stdout_text, stderr_text))
            if len(samples) >= limit:
                return samples
    return samples


def run_parser_demo(
    parser_name: str,
    parse_func: Callable[[str, str], dict[str, Any]],
    tool_key: str,
    inspect_prefix: str,
    limit: int = 5,
) -> int:
    """Run parser over local sample files for a quick smoke test."""
    samples = load_tool_samples(
        tool_key=tool_key,
        inspect_prefix=inspect_prefix,
        limit=limit,
    )
    if not samples:
        print(
            f"[{parser_name}] no sample files found under "
            "eval/results/raw or eval/results/inspect."
        )
        return 0

    for idx, (sample_name, raw_output, raw_stderr) in enumerate(samples, start=1):
        result = parse_func(raw_output, raw_stderr)
        print("=" * 80)
        print(f"[{parser_name}] sample#{idx}: {sample_name}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
