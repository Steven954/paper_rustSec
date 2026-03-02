"""Parser for MirChecker outputs."""

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

DIAG_HEADER_RE = re.compile(
    r"^\s*(?P<level>fatal error|error|warning|bug|unsafe)"
    r"\s*(?:\[(?P<rule>[^\]]+)\])?\s*:\s*(?P<message>.+?)\s*$",
    re.IGNORECASE,
)

# 只有 MirChecker 的确定错误或可能错误才计为漏洞检出
MIRCHECKER_SECURITY_PATTERN = re.compile(
    r"\[MirChecker\]\s+(?:Provably|Possible)\s+error",
    re.IGNORECASE,
)


def _is_mirchecker_security_alert(text: str) -> bool:
    """仅当输出包含 [MirChecker] Provably error 或 [MirChecker] Possible error 时视为漏洞检出。"""
    return bool(MIRCHECKER_SECURITY_PATTERN.search(text or ""))


def _looks_like_diagnostic(line: str) -> bool:
    return bool(DIAG_HEADER_RE.match(line))


def parse(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    """Parse MirChecker stdout/stderr and return normalized alerts."""
    stdout = strip_ansi(raw_output)
    stderr = strip_ansi(raw_stderr)
    merged = "\n".join([stdout, stderr])
    lines = merged.splitlines()

    alerts: list[dict[str, Any]] = []

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        header = DIAG_HEADER_RE.match(line)
        if header:
            message = header.group("message").strip()
            if not _is_mirchecker_security_alert(message):
                continue

            level = header.group("level").strip().lower()
            rule_id = (header.group("rule") or "").strip() or None
            message = f"{level}: {message}"

            location = extract_location(line)
            if not location:
                for look_ahead in range(idx + 1, min(idx + 8, len(lines))):
                    candidate = lines[look_ahead].strip()
                    if not candidate:
                        continue
                    candidate_loc = extract_location(candidate)
                    if candidate_loc:
                        location = candidate_loc
                        break
                    if _looks_like_diagnostic(candidate):
                        break

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

        parsed = parse_file_line_message(line)
        if parsed:
            file_path, line_no, message = parsed
            if _is_mirchecker_security_alert(message):
                alerts.append(
                    make_alert(
                        file_path=file_path,
                        line=line_no,
                        message=message,
                        rule_id=None,
                    )
                )

    if not alerts:
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if not _is_mirchecker_security_alert(line):
                continue
            if not (_looks_like_diagnostic(line) or extract_location(line)):
                continue

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
                    rule_id=None,
                )
            )

    alerts = dedupe_alerts(alerts)
    return {
        "detected": bool(alerts),
        "alerts": alerts,
    }


def main() -> int:
    return run_parser_demo(
        parser_name="mirchecker",
        parse_func=parse,
        tool_key="mirchecker",
        inspect_prefix="MirChecker",
    )


if __name__ == "__main__":
    raise SystemExit(main())
