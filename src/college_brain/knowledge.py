from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import yaml

from .knowledge_split import SourceSegment, chunk_text, split_transcript
from .markdown import atomic_write, write_markdown
from .models import KnowledgeSourceMeta, dumpable
from .vault import utc_now


@dataclass(frozen=True)
class SearchResult:
    source_id: str
    title: str
    content: str
    score: float
    citation: str
    source_path: str
    published_at: str | None
    match_type: str


class EmbeddingClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.environ.get("BRAIN_EMBEDDING_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("BRAIN_EMBEDDING_API_KEY")
        self.model = model or os.environ.get("BRAIN_EMBEDDING_MODEL", "")

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.configured:
            return []
        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]


class KnowledgeIndex:
    CACHE_SCHEMA_VERSION = "2"

    @staticmethod
    def _search_tokens(text: str) -> str:
        ascii_words = re.findall(r"[A-Za-z0-9_-]{2,}", text.lower())
        chinese_groups = re.findall(r"[\u4e00-\u9fff]+", text)
        chinese_tokens: list[str] = []
        for group in chinese_groups:
            chinese_tokens.extend(group)
            chinese_tokens.extend(group[index : index + 2] for index in range(len(group) - 1))
        return " ".join([*ascii_words, *chinese_tokens])

    def __init__(self, root: Path):
        self.root = root
        self.db_path = root / ".brain/knowledge.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        existing_tables = {
            row["name"]
            for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        try:
            version = self.connection.execute("SELECT value FROM cache_meta WHERE key='schema_version'").fetchone()
        except sqlite3.OperationalError:
            version = None
        stale_cache = bool(existing_tables) and (
            version is None or version["value"] != self.CACHE_SCHEMA_VERSION
        )
        if stale_cache:
            self.connection.close()
            self.db_path.unlink()
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS cache_meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources (
              source_id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              path TEXT NOT NULL,
              published_at TEXT,
              imported_at TEXT NOT NULL,
              source_revision TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
              chunk_id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL REFERENCES sources(source_id),
              ordinal INTEGER NOT NULL,
              content TEXT NOT NULL,
              start_line INTEGER NOT NULL,
              end_line INTEGER NOT NULL,
              embedding TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
              chunk_id UNINDEXED,
              source_id UNINDEXED,
              title,
              content
            );
            """
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO cache_meta(key,value) VALUES('schema_version',?)",
            (self.CACHE_SCHEMA_VERSION,),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def import_transcript(
        self,
        source_file: Path,
        *,
        advisor: str = "unknown",
        platform: str | None = None,
        source_url: str | None = None,
        published_at: str | None = None,
        copyright_status: str = "undetermined",
        batch_id: str | None = None,
        heading_level: int = 1,
        delimiter: str | None = None,
        dry_run: bool = False,
    ) -> list[SourceSegment]:
        effective_batch = batch_id or source_file.stem
        segments = split_transcript(
            source_file.read_text(encoding="utf-8"),
            namespace=effective_batch,
            heading_level=heading_level,
            delimiter=delimiter,
        )
        if dry_run:
            return segments
        source_dir = self.root / "knowledge/sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        catalog_path = self.root / "knowledge/catalog.yaml"
        catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"schema_version": 5, "sources": []}
        existing = {item.get("source_id"): item for item in catalog.get("sources", [])}
        imported_at = utc_now()
        new_source_ids = {segment.source_id for segment in segments}
        stale_ids = {
            source_id
            for source_id, item in existing.items()
            if item.get("import_key") == effective_batch and source_id not in new_source_ids
        }
        for stale_id in stale_ids:
            stale_item = existing.pop(stale_id)
            stale_path = self.root / stale_item.get("path", "")
            if stale_path.is_file():
                stale_path.unlink()
        for segment in segments:
            body = f"# {segment.title}\n\n{segment.body}\n"
            metadata = KnowledgeSourceMeta(
                id=segment.source_id,
                title=segment.title,
                advisor=advisor,
                platform=platform,
                source_url=source_url,
                published_at=published_at,
                imported_at=imported_at,
                created_at=imported_at,
                updated_at=imported_at,
                import_key=effective_batch,
                copyright_status=copyright_status,
            )
            relative = Path("knowledge/sources") / f"{segment.source_id}.md"
            write_markdown(self.root / relative, dumpable(metadata), body)
            existing[segment.source_id] = {
                "source_id": segment.source_id,
                "title": segment.title,
                "path": relative.as_posix(),
                "advisor": advisor,
                "source_url": source_url,
                "published_at": published_at,
                "imported_at": imported_at.isoformat(),
                "import_key": effective_batch,
            }
        catalog["sources"] = sorted(existing.values(), key=lambda item: item["source_id"])
        atomic_write(catalog_path, yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False))
        return segments

    def index_sources(
        self,
        *,
        embed_client: EmbeddingClient | None = None,
        allow_remote_content: bool = False,
    ) -> int:
        client = embed_client or EmbeddingClient()
        indexed = 0
        current_source_ids = set()
        for path in sorted((self.root / "knowledge/sources").glob("*.md")):
            metadata, body = self._read_source(path)
            source_id = metadata["id"]
            current_source_ids.add(source_id)
            source_mtime = str(path.stat().st_mtime_ns)
            endpoint = getattr(client, "base_url", "")
            source_revision = f"{source_mtime}:{endpoint}:{client.model if client.configured and allow_remote_content else 'keyword-only'}"
            existing = self.connection.execute(
                "SELECT source_revision FROM sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            if existing:
                same_content = existing["source_revision"].startswith(f"{source_mtime}:")
                requested_vector_upgrade = allow_remote_content and existing["source_revision"] != source_revision
                if same_content and not requested_vector_upgrade:
                    continue
            self.connection.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            self.connection.execute("DELETE FROM chunks_fts WHERE source_id = ?", (source_id,))
            chunks = chunk_text(body)
            embeddings = client.embed([chunk[0] for chunk in chunks]) if client.configured and allow_remote_content else []
            if embeddings and len(embeddings) != len(chunks):
                raise ValueError(f"embedding 返回数量不匹配：需要 {len(chunks)} 个，收到 {len(embeddings)} 个")
            if embeddings:
                dimensions = {len(vector) for vector in embeddings}
                if len(dimensions) != 1:
                    raise ValueError("embedding 返回向量维度不一致")
            self.connection.execute(
                "INSERT OR REPLACE INTO sources(source_id,title,path,published_at,imported_at,source_revision) VALUES(?,?,?,?,?,?)",
                (source_id, metadata.get("title", path.stem), path.relative_to(self.root).as_posix(), metadata.get("published_at"), metadata.get("imported_at", ""), source_revision),
            )
            for ordinal, ((content, start, end), embedding) in enumerate(zip(chunks, embeddings or [None] * len(chunks))):
                chunk_id = f"{source_id}#{ordinal + 1}"
                encoded = json.dumps(embedding) if embedding is not None else None
                self.connection.execute(
                    "INSERT INTO chunks(chunk_id,source_id,ordinal,content,start_line,end_line,embedding) VALUES(?,?,?,?,?,?,?)",
                    (chunk_id, source_id, ordinal + 1, content, start, end, encoded),
                )
                self.connection.execute(
                    "INSERT INTO chunks_fts(chunk_id,source_id,title,content) VALUES(?,?,?,?)",
                    (
                        chunk_id,
                        source_id,
                        self._search_tokens(metadata.get("title", path.stem)),
                        self._search_tokens(content),
                    ),
                )
                indexed += 1
        for source_id in [row["source_id"] for row in self.connection.execute("SELECT source_id FROM sources") if row["source_id"] not in current_source_ids]:
            self.connection.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            self.connection.execute("DELETE FROM chunks_fts WHERE source_id = ?", (source_id,))
            self.connection.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
        self.connection.commit()
        return indexed

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        embed_client: EmbeddingClient | None = None,
        allow_remote_query: bool = False,
    ) -> list[SearchResult]:
        keyword_results = self._keyword_search(query, limit * 3)
        client = embed_client or EmbeddingClient()
        vector_results = self._vector_search(query, client, limit * 3) if client.configured and allow_remote_query else []
        merged: dict[str, dict[str, Any]] = {}
        for rank, result in enumerate(keyword_results, start=1):
            merged.setdefault(result["chunk_id"], {"keyword": 0.0, "vector": 0.0, "row": result})["keyword"] = 1 / (60 + rank)
        for rank, result in enumerate(vector_results, start=1):
            merged.setdefault(result["chunk_id"], {"keyword": 0.0, "vector": 0.0, "row": result})["vector"] = 1 / (60 + rank)
        ranked = sorted(merged.values(), key=lambda item: -(item["keyword"] + item["vector"]))[:limit]
        return [self._result(item["row"], item["keyword"], item["vector"]) for item in ranked]

    def _read_source(self, path: Path) -> tuple[dict[str, Any], str]:
        from .markdown import read_markdown
        return read_markdown(path)

    def _keyword_search(self, query: str, limit: int) -> list[sqlite3.Row]:
        tokens = list(dict.fromkeys(self._search_tokens(query).split()))
        if not tokens:
            return []
        expression = " OR ".join(f'"{token}"' for token in tokens)
        return list(
            self.connection.execute(
                "SELECT c.*, s.title, s.path, s.published_at FROM chunks_fts f JOIN chunks c ON c.chunk_id=f.chunk_id JOIN sources s ON s.source_id=c.source_id WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?",
                (expression, limit),
            )
        )

    def _vector_search(self, query: str, client: EmbeddingClient, limit: int) -> list[sqlite3.Row]:
        query_embedding = client.embed([query])
        if not query_embedding:
            return []
        query_vector = np.array(query_embedding[0], dtype=float)
        rows = list(self.connection.execute("SELECT c.*, s.title, s.path, s.published_at FROM chunks c JOIN sources s ON s.source_id=c.source_id WHERE c.embedding IS NOT NULL"))
        scored = []
        for row in rows:
            vector = np.array(json.loads(row["embedding"]), dtype=float)
            if vector.shape != query_vector.shape:
                continue
            denominator = np.linalg.norm(query_vector) * np.linalg.norm(vector)
            score = float(np.dot(query_vector, vector) / denominator) if denominator else 0.0
            scored.append((score, row))
        return [row for _, row in sorted(scored, key=lambda item: -item[0])[:limit]]

    @staticmethod
    def _result(row: sqlite3.Row, keyword_score: float, vector_score: float) -> SearchResult:
        match_type = "关键词+向量" if keyword_score and vector_score else "关键词" if keyword_score else "向量"
        return SearchResult(
            source_id=row["source_id"],
            title=row["title"],
            content=row["content"],
            score=keyword_score + vector_score,
            citation=f"{row['source_id']}#{row['ordinal']}（正文第 {row['start_line']}-{row['end_line']} 行；文件含 frontmatter）",
            source_path=row["path"],
            published_at=row["published_at"],
            match_type=match_type,
        )
