"""Parser for FFIChecker outputs."""

from __future__ import annotations

import re
from typing import Any

try:
    from ._common import (
        dedupe_alerts,
        extract_location,
        has_alert_keywords,
        make_alert,
        parse_file_line_message,
        run_parser_demo,
        strip_ansi,
    )
except ImportError:
    from _common import (
        dedupe_alerts,
        extract_location,
        has_alert_keywords,
        make_alert,
        parse_file_line_message,
        run_parser_demo,
        strip_ansi,
    )

BUG_INFO_RE = re.compile(
    r'^\s*\(\s*"?(?P<function>[^",)]+)"?\s*,\s*Bug info:\s*(?P<info>.+?)\)\s*$',
    re.IGNORECASE,
)
POSSIBLE_BUGS_RE = re.compile(
    r"Possible bugs:\s*(?P<bugs>.+?)(?:,\s*seriousness:|$)",
    re.IGNORECASE,
)


def _extract_rule_id(message: str) -> str | None:
    match = POSSIBLE_BUGS_RE.search(message)
    if not match:
        return None
    return match.group("bugs").strip(" .") or None


def parse(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    """Parse FFIChecker stdout/stderr and return normalized alerts."""
    stdout = strip_ansi(raw_output)
    stderr = strip_ansi(raw_stderr)
    merged = "\n".join([stdout, stderr])
    lines = merged.splitlines()

    alerts: list[dict[str, Any]] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        bug_match = BUG_INFO_RE.match(line)
        if bug_match:
            function_name = bug_match.group("function").strip()
            bug_info = bug_match.group("info").strip()
            message = f"{function_name}: {bug_info}"
            rule_id = _extract_rule_id(bug_info)
            location = extract_location(line)
            if location:
                file_path, line_no = location
            else:
                file_path, line_no = ("", 0)
            alerts.append(
                make_alert(
                    file_path=file_path,
                    line=line_no,
                    message=message,
                    rule_id=rule_id,
                )
            )
            continue

        if "Bug info:" in line or "Possible bugs:" in line:
            rule_id = _extract_rule_id(line)
            location = extract_location(line)
            if location:
                file_path, line_no = location
            else:
                file_path, line_no = ("", 0)
            alerts.append(
                make_alert(
                    file_path=file_path,
                    line=line_no,
                    message=line,
                    rule_id=rule_id,
                )
            )
            continue

        parsed = parse_file_line_message(line)
        if parsed:
            file_path, line_no, message = parsed
            # Only accept file:line:message lines that contain FFIChecker security patterns
            # (e.g. "Possible bugs", "Use After Free") to avoid compiler warnings.
            if ("Possible bugs:" in message or "Bug info:" in message) and has_alert_keywords(
                message
            ):
                alerts.append(
                    make_alert(
                        file_path=file_path,
                        line=line_no,
                        message=message,
                        rule_id=None,
                    )
                )

    # No fallback: do not add generic "error"/"warning" lines - they cause false positives
    # (e.g. "fatal error: Could not obtain Cargo metadata", "Compiling quick-error").
    alerts = dedupe_alerts(alerts)
    # Only count as detected when we have parsed security alerts (Bug info / Possible bugs).
    # Do NOT use keyword_detected fallback - it causes false positives from compiler output
    # (e.g. "fatal error", "warning: unused variable", "Compiling quick-error").
    return {
        "detected": bool(alerts),
        "alerts": alerts,
    }


def main() -> int:
    return run_parser_demo(
        parser_name="ffichecker",
        parse_func=parse,
        tool_key="ffichecker",
        inspect_prefix="FFIChecker",
    )


if __name__ == "__main__":
    raise SystemExit(main())
