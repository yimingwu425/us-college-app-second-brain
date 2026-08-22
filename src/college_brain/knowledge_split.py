from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSegment:
    source_id: str
    title: str
    body: str
    ordinal: int
    start_line: int
    end_line: int


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
SEPARATOR_RE = re.compile(r"^\s*(?:={3,}|-{3,}|视频\s*[:：].*)\s*$", re.IGNORECASE)


def stable_source_id(namespace: str, title: str, occurrence: int = 1) -> str:
    namespace_slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", namespace.strip().lower()).strip("-") or "batch"
    title_slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.strip().lower()).strip("-") or "video"
    suffix = f"-{occurrence}" if occurrence > 1 else ""
    return f"src-{namespace_slug}-{title_slug}{suffix}"


def split_transcript(
    text: str,
    *,
    namespace: str = "batch",
    heading_level: int = 1,
    delimiter: str | None = None,
) -> list[SourceSegment]:
    lines = text.splitlines()
    video_line = re.compile(r"^\s*视频\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)
    separator = re.compile(
        rf"^\s*{re.escape(delimiter)}\s*$" if delimiter else SEPARATOR_RE.pattern,
        re.IGNORECASE,
    )
    title_re = re.compile(rf"^\s*#{{{heading_level}}}\s+(.+?)\s*$")

    separators = [index for index, line in enumerate(lines) if separator.match(line)]
    if separators and (delimiter or not any(HEADING_RE.match(line) or video_line.match(line) for line in lines)):
        spans: list[tuple[int, int]] = []
        start = 0
        for separator_index in separators:
            spans.append((start, separator_index))
            start = separator_index + 1
        spans.append((start, len(lines)))
        segments: list[SourceSegment] = []
        id_occurrences: dict[str, int] = {}
        for ordinal, (span_start, span_end) in enumerate(spans, start=1):
            span_lines = lines[span_start:span_end]
            title = ""
            body_lines = span_lines
            for local_index, line in enumerate(span_lines):
                heading = title_re.match(line) or video_line.match(line)
                if heading:
                    title = heading.group(1).strip()
                    body_lines = span_lines[local_index + 1 :]
                    span_start += local_index
                    break
            body = "\n".join(body_lines).strip()
            if not body:
                continue
            actual_title = title or f"视频 {ordinal}"
            base_id = stable_source_id(namespace, actual_title)
            id_occurrences[base_id] = id_occurrences.get(base_id, 0) + 1
            occurrence = id_occurrences[base_id]
            segments.append(
                SourceSegment(
                    source_id=stable_source_id(namespace, actual_title, occurrence),
                    title=actual_title,
                    body=body,
                    ordinal=ordinal,
                    start_line=span_start + 1,
                    end_line=span_end,
                )
            )
        return segments

    boundaries: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        named_video = video_line.match(line)
        if match and len(match.group(1)) == heading_level:
            boundaries.append((index, match.group(2).strip()))
        elif named_video:
            boundaries.append((index, named_video.group(1).strip()))

    if not boundaries:
        body = text.strip()
        return [SourceSegment(stable_source_id(namespace, "未命名视频"), "未命名视频", body, 1, 1, len(lines))] if body else []

    segments = []
    id_occurrences: dict[str, int] = {}
    for ordinal, (start, title) in enumerate(boundaries, start=1):
        end = boundaries[ordinal][0] if ordinal < len(boundaries) else len(lines)
        body = "\n".join(lines[start + 1 : end]).strip()
        if not body:
            continue
        base_id = stable_source_id(namespace, title)
        id_occurrences[base_id] = id_occurrences.get(base_id, 0) + 1
        occurrence = id_occurrences[base_id]
        segments.append(
            SourceSegment(
                source_id=stable_source_id(namespace, title, occurrence),
                title=title,
                body=body,
                ordinal=ordinal,
                start_line=start + 1,
                end_line=end,
            )
        )
    return segments


def chunk_text(text: str, *, max_chars: int = 900, overlap: int = 120) -> list[tuple[str, int, int]]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[tuple[str, int, int]] = []
    current = ""
    start = 1
    cursor = 0
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append((current, start, cursor))
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{paragraph}" if tail else paragraph
            start = cursor
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
        cursor += len(paragraph.splitlines()) + 1
    if current:
        chunks.append((current, start, cursor))
    return chunks
