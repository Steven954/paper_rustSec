"""Parsers for normalizing tool-specific outputs into alert records."""

from __future__ import annotations

from typing import Any

__all__ = ["parse_rudra", "parse_mirchecker", "parse_ffichecker"]


def parse_rudra(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    from .rudra import parse

    return parse(raw_output, raw_stderr)


def parse_mirchecker(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    from .mirchecker import parse

    return parse(raw_output, raw_stderr)


def parse_ffichecker(raw_output: str, raw_stderr: str) -> dict[str, Any]:
    from .ffichecker import parse

    return parse(raw_output, raw_stderr)
