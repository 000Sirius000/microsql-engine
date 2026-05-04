from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from microsql.exceptions import FileSystemException
from microsql.parser import ParserOptions


@dataclass(frozen=True, slots=True)
class AppConfig:
    filter_engine: str = "specification"
    enable_not_operator: bool = True
    case_sensitive_strings: bool = True

    @classmethod
    def safe_default(cls) -> AppConfig:
        return cls()

    def to_parser_options(self) -> ParserOptions:
        return ParserOptions(
            filter_engine=self.filter_engine,
            enable_not_operator=self.enable_not_operator,
            case_sensitive_strings=self.case_sensitive_strings,
        )


def load_config(config_path: Path | None) -> AppConfig:
    """Load optional JSON configuration or return safe defaults when it is absent."""

    if config_path is None or not config_path.exists():
        return AppConfig.safe_default()

    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FileSystemException(
            f"Invalid JSON configuration: {config_path} ({error.msg})",
            error.lineno,
        ) from error
    except OSError as error:
        raise FileSystemException(
            f"Cannot read configuration file: {config_path} ({error})",
            1,
        ) from error

    if not isinstance(raw_config, dict):
        return AppConfig.safe_default()

    return _config_from_mapping(raw_config)


def _config_from_mapping(raw_config: dict[str, Any]) -> AppConfig:
    filter_section = raw_config.get("filter", {})
    if not isinstance(filter_section, dict):
        filter_section = {}

    filter_engine = _read_string(
        filter_section,
        "engine",
        default="specification",
        allowed={"specification"},
    )
    enable_not_operator = _read_bool(filter_section, "enable_not_operator", default=True)
    case_sensitive_strings = _read_bool(filter_section, "case_sensitive_strings", default=True)

    return AppConfig(
        filter_engine=filter_engine,
        enable_not_operator=enable_not_operator,
        case_sensitive_strings=case_sensitive_strings,
    )


def _read_string(
    source: dict[str, Any],
    key: str,
    default: str,
    allowed: set[str],
) -> str:
    value = source.get(key, default)
    if not isinstance(value, str):
        return default
    normalized = value.strip().lower()
    if normalized not in allowed:
        return default
    return normalized


def _read_bool(source: dict[str, Any], key: str, default: bool) -> bool:
    value = source.get(key, default)
    if not isinstance(value, bool):
        return default
    return value
