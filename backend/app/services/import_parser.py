import csv
import io
import json
from dataclasses import dataclass, field

from app.core.language import SupportedLanguage
from app.models.dataset import LabelType, MessageRole


class ImportParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class ParsedExample:
    external_id: str | None
    messages: list[ParsedMessage]
    labels: dict[LabelType, str] = field(default_factory=dict)
    language: SupportedLanguage | None = None


def parse_import_content(source_type: str, content: str) -> list[ParsedExample]:
    if source_type == "jsonl":
        return parse_jsonl(content)
    if source_type == "csv":
        return parse_csv(content)
    raise ImportParseError("Unsupported source_type.")


def parse_jsonl(content: str) -> list[ParsedExample]:
    examples: list[ParsedExample] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ImportParseError(f"Invalid JSONL at line {line_number}.") from exc
        examples.append(_parse_jsonl_example(payload, line_number))

    if not examples:
        raise ImportParseError("Import content did not contain any examples.")
    return examples


def parse_csv(content: str) -> list[ParsedExample]:
    reader = csv.DictReader(io.StringIO(content), strict=True)
    try:
        return _parse_csv_rows(reader)
    except csv.Error as exc:
        raise ImportParseError(f"Malformed CSV near line {reader.line_num}.") from exc


def _parse_csv_rows(reader: csv.DictReader) -> list[ParsedExample]:
    required_columns = {"role", "content"}
    if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
        raise ImportParseError("CSV must include role and content columns.")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ImportParseError("CSV column names must be unique.")

    examples: list[ParsedExample] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise ImportParseError(f"CSV row {row_number} has more fields than its header.")
        role = _parse_role(row.get("role"), f"row {row_number}")
        message_content = (row.get("content") or "").strip()
        if not message_content:
            raise ImportParseError(f"CSV row {row_number} has empty content.")
        labels = _parse_label_columns(row)
        examples.append(
            ParsedExample(
                external_id=(row.get("external_id") or "").strip() or None,
                messages=[ParsedMessage(role=role, content=message_content)],
                labels=labels,
                language=_parse_language(row.get("language"), f"row {row_number}"),
            )
        )

    if not examples:
        raise ImportParseError("CSV did not contain any examples.")
    return examples


def _parse_jsonl_example(payload: object, line_number: int) -> ParsedExample:
    if not isinstance(payload, dict):
        raise ImportParseError(f"JSONL line {line_number} must be an object.")
    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ImportParseError(f"JSONL line {line_number} must include non-empty messages.")

    messages: list[ParsedMessage] = []
    for index, raw_message in enumerate(raw_messages, start=1):
        if not isinstance(raw_message, dict):
            raise ImportParseError(f"JSONL line {line_number} message {index} must be an object.")
        role = _parse_role(raw_message.get("role"), f"line {line_number} message {index}")
        raw_content = raw_message.get("content")
        if not isinstance(raw_content, str):
            raise ImportParseError(
                f"JSONL line {line_number} message {index} content must be a string.")
        message_content = raw_content.strip()
        if not message_content:
            raise ImportParseError(f"JSONL line {line_number} message {index} has empty content.")
        messages.append(ParsedMessage(role=role, content=message_content))

    labels = _parse_json_labels(payload.get("labels"), line_number)
    external_id = payload.get("external_id")
    return ParsedExample(
        external_id=str(external_id).strip() if external_id is not None else None,
        messages=messages,
        labels=labels,
        language=_parse_language(payload.get("language"), f"line {line_number}"),
    )


def _parse_language(value: object, location: str) -> SupportedLanguage | None:
    if value is None or value == "":
        return None
    try:
        return SupportedLanguage(value)
    except (ValueError, TypeError) as exc:
        raise ImportParseError(f"Unsupported language at {location}; use en, ja or zh.") from exc


def _parse_role(value: object, location: str) -> MessageRole:
    try:
        return MessageRole(str(value).strip())
    except ValueError as exc:
        raise ImportParseError(f"Invalid role at {location}.") from exc


def _parse_json_labels(value: object, line_number: int) -> dict[LabelType, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ImportParseError(f"JSONL line {line_number} labels must be an object.")

    labels: dict[LabelType, str] = {}
    for raw_type, raw_value in value.items():
        label_type = _parse_label_type(raw_type, f"line {line_number}")
        label_value = str(raw_value).strip()
        if label_value:
            labels[label_type] = label_value
    return labels


def _parse_label_columns(row: dict[str, str | None]) -> dict[LabelType, str]:
    labels: dict[LabelType, str] = {}
    for column, value in row.items():
        if not column.startswith("label_") or value is None:
            continue
        label_name = column.removeprefix("label_")
        label_value = value.strip()
        if not label_value:
            continue
        labels[_parse_label_type(label_name, f"column {column}")] = label_value
    return labels


def _parse_label_type(value: object, location: str) -> LabelType:
    try:
        return LabelType(str(value).strip())
    except ValueError as exc:
        raise ImportParseError(f"Unsupported label type at {location}.") from exc
