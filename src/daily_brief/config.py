"""Configuration loading with a tiny YAML/JSON fallback parser.

PyYAML is intentionally optional. The bundled configuration uses a conservative
subset of YAML (nested mappings plus lists of mappings) that this parser
supports. JSON is also accepted because it is a YAML subset.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a configuration file is missing or invalid."""


@dataclass(slots=True)
class ProjectConfig:
    name: str
    timezone: str = "Asia/Shanghai"


@dataclass(slots=True)
class ScheduleConfig:
    time: str = "07:00"


@dataclass(slots=True)
class PathsConfig:
    report: str
    memory: str
    run_dir: str
    push_payload: str


@dataclass(slots=True)
class SectionConfig:
    id: str
    title: str
    description: str = ""


@dataclass(slots=True)
class SourceConfig:
    id: str
    type: str
    name: str
    enabled: bool = True
    url: str = ""
    path: str = ""
    max_items: int = 20
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ThresholdsConfig:
    min_loops: int = 5
    max_loops: int = 10
    default_loops: int = 7
    pass_score: float = 8.0
    duplicate_jaccard: float = 0.78
    related_jaccard: float = 0.30


@dataclass(slots=True)
class PushConfig:
    codex_app_webhook_url_env: str
    adapter: str = "codex_app_webhook"
    dry_run_without_webhook: bool = True


@dataclass(slots=True)
class BriefConfig:
    project: ProjectConfig
    schedule: ScheduleConfig
    paths: PathsConfig
    sections: list[SectionConfig]
    sources: list[SourceConfig]
    thresholds: ThresholdsConfig
    push: PushConfig
    raw: dict[str, Any] = field(default_factory=dict)


_REQUIRED_SECTION_IDS = {
    "tech_news",
    "tool_engineering",
    "social_blogs",
    "video",
    "product_ideas",
}
_ALLOWED_SOURCE_TYPES = {
    "fixture",
    "rss",
    "reddit",
    "youtube",
    "browser_prompts",
    "telegram",
    "github_updates",
}


def load_config(path: str | Path) -> BriefConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"config file not found: {config_path}")
    text = config_path.read_text(encoding="utf-8")
    data = _load_mapping(text)
    return _build_config(data)


def _load_mapping(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ConfigError("config file is empty")

    # JSON first, so a .yaml file can be supplied with a JSON document.
    try:
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ConfigError("top-level config must be a mapping")
        return parsed
    except json.JSONDecodeError:
        pass

    # Optional PyYAML support when already available; never required.
    try:  # pragma: no cover - optional dependency path
        import yaml  # type: ignore

        parsed = yaml.safe_load(stripped)
        if not isinstance(parsed, dict):
            raise ConfigError("top-level config must be a mapping")
        return parsed
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # fall through to fallback parser with context
        fallback_error = exc
    else:  # pragma: no cover
        fallback_error = None

    try:
        parsed = _parse_simple_yaml(stripped)
    except Exception as exc:  # noqa: BLE001 - convert parser details to config error
        if "fallback_error" in locals() and fallback_error:
            raise ConfigError(f"could not parse config as YAML: {fallback_error}; fallback failed: {exc}") from exc
        raise ConfigError(f"could not parse config as YAML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("top-level config must be a mapping")
    return parsed


def _build_config(data: dict[str, Any]) -> BriefConfig:
    try:
        project_data = _require_mapping(data, "project")
        schedule_data = _require_mapping(data, "schedule")
        paths_data = _require_mapping(data, "paths")
        sections_data = _require_list(data, "sections")
        sources_data = _require_list(data, "sources")
        thresholds_data = _require_mapping(data, "thresholds")
        push_data = _require_mapping(data, "push")
    except KeyError as exc:
        raise ConfigError(f"missing required config key: {exc.args[0]}") from exc

    project = ProjectConfig(
        name=str(project_data.get("name", "")).strip(),
        timezone=str(project_data.get("timezone", "Asia/Shanghai")).strip(),
    )
    if project.name != "daily-brief":
        raise ConfigError("project.name must be daily-brief")

    schedule = ScheduleConfig(time=str(schedule_data.get("time", "")).strip())
    if not re.fullmatch(r"[0-2]\d:[0-5]\d", schedule.time):
        raise ConfigError("schedule.time must be HH:MM")

    paths = PathsConfig(
        report=_required_str(paths_data, "report"),
        memory=_required_str(paths_data, "memory"),
        run_dir=_required_str(paths_data, "run_dir"),
        push_payload=_required_str(paths_data, "push_payload"),
    )

    sections = [
        SectionConfig(
            id=_required_str(section, "id"),
            title=_required_str(section, "title"),
            description=str(section.get("description", "")),
        )
        for section in sections_data
        if isinstance(section, dict)
    ]
    if len(sections) < 5:
        raise ConfigError("sections must contain the five required report sections")
    section_ids = {section.id for section in sections}
    missing_sections = sorted(_REQUIRED_SECTION_IDS - section_ids)
    if missing_sections:
        raise ConfigError(f"missing required sections: {', '.join(missing_sections)}")

    sources: list[SourceConfig] = []
    for raw_source in sources_data:
        if not isinstance(raw_source, dict):
            raise ConfigError("sources entries must be mappings")
        source_type = _required_str(raw_source, "type")
        if source_type not in _ALLOWED_SOURCE_TYPES:
            raise ConfigError(f"unsupported source type: {source_type}")
        known = {"id", "type", "name", "enabled", "url", "path", "max_items"}
        sources.append(
            SourceConfig(
                id=_required_str(raw_source, "id"),
                type=source_type,
                name=_required_str(raw_source, "name"),
                enabled=bool(raw_source.get("enabled", True)),
                url=str(raw_source.get("url", "")),
                path=str(raw_source.get("path", "")),
                max_items=int(raw_source.get("max_items", 20)),
                metadata={key: value for key, value in raw_source.items() if key not in known},
            )
        )
    if not sources:
        raise ConfigError("at least one source must be configured")

    thresholds = ThresholdsConfig(
        min_loops=int(thresholds_data.get("min_loops", 5)),
        max_loops=int(thresholds_data.get("max_loops", 10)),
        default_loops=int(thresholds_data.get("default_loops", 7)),
        pass_score=float(thresholds_data.get("pass_score", 8.0)),
        duplicate_jaccard=float(thresholds_data.get("duplicate_jaccard", 0.78)),
        related_jaccard=float(thresholds_data.get("related_jaccard", 0.30)),
    )
    if thresholds.min_loops < 5 or thresholds.max_loops > 10 or thresholds.min_loops > thresholds.max_loops:
        raise ConfigError("thresholds must enforce 5 <= min_loops <= max_loops <= 10")
    if not (thresholds.min_loops <= thresholds.default_loops <= thresholds.max_loops):
        raise ConfigError("thresholds.default_loops must be within min/max")

    push = PushConfig(
        adapter=str(push_data.get("adapter", "codex_app_webhook")),
        codex_app_webhook_url_env=_required_str(push_data, "codex_app_webhook_url_env"),
        dry_run_without_webhook=bool(push_data.get("dry_run_without_webhook", True)),
    )
    if any(secret in json.dumps(data, ensure_ascii=False).lower() for secret in ("password", "cookie", "session")):
        raise ConfigError("config must not contain password/cookie/session fields")

    return BriefConfig(
        project=project,
        schedule=schedule,
        paths=paths,
        sections=sections,
        sources=sources,
        thresholds=thresholds,
        push=push,
        raw=data,
    )


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data[key]
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a mapping")
    return value


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data[key]
    if not isinstance(value, list):
        raise ConfigError(f"{key} must be a list")
    return value


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or not str(value).strip():
        raise ConfigError(f"missing required string: {key}")
    return str(value).strip()


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
    return line.rstrip()


def _parse_simple_yaml(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = _strip_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise ConfigError("fallback YAML parser expects two-space indentation")
        lines.append((indent, line.strip()))
    if not lines:
        return {}
    parsed, next_index = _parse_block(lines, 0, lines[0][0])
    if next_index != len(lines):
        raise ConfigError("unexpected trailing YAML content")
    return parsed


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, current_content = lines[index]
    if current_indent < indent:
        return {}, index
    if current_content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent != indent or not content.startswith("- "):
            break
        rest = content[2:].strip()
        index += 1
        if not rest:
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
            else:
                child = None
            result.append(child)
            continue
        if _looks_like_key_value(rest):
            key, raw_value = _split_key_value(rest)
            item: dict[str, Any] = {}
            if raw_value == "":
                if index < len(lines) and lines[index][0] > indent:
                    child, index = _parse_block(lines, index, lines[index][0])
                else:
                    child = {}
                item[key] = child
            else:
                item[key] = _parse_scalar(raw_value)
            if index < len(lines) and lines[index][0] > indent:
                extra, index = _parse_block(lines, index, lines[index][0])
                if isinstance(extra, dict):
                    item.update(extra)
                else:
                    item["items"] = extra
            result.append(item)
        else:
            result.append(_parse_scalar(rest))
            if index < len(lines) and lines[index][0] > indent:
                raise ConfigError("scalar list entries cannot have nested blocks in fallback parser")
    return result, index


def _parse_mapping(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ConfigError(f"unexpected indentation near: {content}")
        if content.startswith("- "):
            break
        if not _looks_like_key_value(content):
            raise ConfigError(f"expected key: value line, got: {content}")
        key, raw_value = _split_key_value(content)
        index += 1
        if raw_value == "":
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
            else:
                child = {}
            result[key] = child
        else:
            result[key] = _parse_scalar(raw_value)
    return result, index


def _looks_like_key_value(value: str) -> bool:
    if ":" not in value:
        return False
    key, _sep, _rest = value.partition(":")
    return bool(key.strip()) and not key.strip().startswith(("'", '"'))


def _split_key_value(value: str) -> tuple[str, str]:
    key, _sep, raw_value = value.partition(":")
    key = key.strip()
    if not key:
        raise ConfigError("empty YAML key")
    return key, raw_value.strip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "''", '""'}:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)", value):
        try:
            return float(value)
        except ValueError:
            pass
    return value
