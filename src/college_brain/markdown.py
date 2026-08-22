from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


class MarkdownFormatError(ValueError):
    pass


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise MarkdownFormatError(f"Missing YAML frontmatter: {path}")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise MarkdownFormatError(f"Unclosed YAML frontmatter: {path}")
    raw_meta = text[4:closing]
    try:
        metadata = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError as exc:
        raise MarkdownFormatError(f"Invalid YAML frontmatter: {path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise MarkdownFormatError(f"Frontmatter must be a mapping: {path}")
    return metadata, text[closing + 5 :]


def render_markdown(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{body.rstrip()}\n"


def write_markdown(path: Path, metadata: dict[str, Any], body: str) -> None:
    atomic_write(path, render_markdown(metadata, body))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
