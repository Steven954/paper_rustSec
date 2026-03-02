"""Parser for Rudra outputs."""

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

RUDRA_WARNING_RE = re.compile(
    r"^\s*Warning\s+\((?P<rule>[^)]+)\):\s*(?P<message>.+?)\s*$"
)
DIAG_PREFIX_RE = re.compile(r"^\s*(?:warning|warn|error|fatal|bug)\b", re.IGNORECASE)


def _is_progress_line(line: str) -> bool:
    lowered = line.lower()
    if "[rudra-progress]" in lowered:
        return True
    if "|info |" in lowered and "rudra" in lowered:
        return True
    return False


def parse(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    """Parse Rudra stdout/stderr and return normalized alerts."""
    stdout = strip_ansi(raw_output)
    stderr = strip_ansi(raw_stderr)
    merged = "\n".join([stdout, stderr])
    lines = merged.splitlines()

    alerts: list[dict[str, Any]] = []

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        warning_match = RUDRA_WARNING_RE.match(line)
        if warning_match:
            message = warning_match.group("message").strip()
            rule_id = warning_match.group("rule").strip() or None
            file_path = ""
            line_no = 0

            for look_ahead in range(idx + 1, min(idx + 8, len(lines))):
                location = extract_location(lines[look_ahead])
                if location:
                    file_path, line_no = location
                    break
                if RUDRA_WARNING_RE.match(lines[look_ahead].strip()):
                    break

            alerts.append(
                make_alert(
                    file_path=file_path,
                    line=line_no,
                    message=message,
                    rule_id=rule_id,
                )
            )
            continue

        parsed = parse_file_line_message(line)
        if parsed:
            file_path, line_no, message = parsed
            if has_alert_keywords(message):
                alerts.append(
                    make_alert(
                        file_path=file_path,
                        line=line_no,
                        message=message,
                        rule_id=None,
                    )
                )

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if alerts:
            break
        if _is_progress_line(line):
            continue
        if not has_alert_keywords(line):
            continue

        location = extract_location(line)
        if location or DIAG_PREFIX_RE.match(line):
            if location:
                file_path, line_no = location
            else:
                file_path, line_no = ("", 0)
            alerts.append(
                make_alert(
                    file_path=file_path,
                    line=line_no,
                    message=line,
                    rule_id=None,
                )
            )

    alerts = dedupe_alerts(alerts)
    keyword_detected = any(
        has_alert_keywords(line)
        and not _is_progress_line(line.strip())
        and (DIAG_PREFIX_RE.match(line.strip()) or extract_location(line))
        for line in lines
        if line.strip()
    )
    return {
        "detected": bool(alerts) or keyword_detected,
        "alerts": alerts,
    }


def main() -> int:
    return run_parser_demo(
        parser_name="rudra",
        parse_func=parse,
        tool_key="rudra",
        inspect_prefix="Rudra",
    )


if __name__ == "__main__":
    raise SystemExit(main())
