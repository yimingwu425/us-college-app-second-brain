from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from college_brain.knowledge import EmbeddingClient, KnowledgeIndex
from college_brain.knowledge_split import split_transcript
from college_brain.vault import init_vault


class FakeEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        self.model = "fake-embedding-v1"
        self.calls: list[list[str]] = []

    @property
    def configured(self) -> bool:
        return True

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        vectors = []
        for text in texts:
            vectors.append([float("文书" in text), float("选校" in text), 0.5])
        return vectors


@pytest.fixture
def knowledge_vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    init_vault(root, timezone="Asia/Shanghai", cycle="2027-08")
    return root


def test_split_combined_markdown_by_heading_and_batch() -> None:
    segments = split_transcript("# 选校\n看匹配。\n# 文书\n写场景。", namespace="advisor-2026")
    assert [item.title for item in segments] == ["选校", "文书"]
    assert segments[0].source_id == "src-advisor-2026-选校"


def test_source_id_survives_reordering() -> None:
    first = split_transcript("# 选校\n看匹配。\n# 文书\n写场景。", namespace="advisor-2026")
    reordered = split_transcript("# 新视频\n新内容。\n# 选校\n看匹配。\n# 文书\n写场景。", namespace="advisor-2026")
    first_ids = {item.title: item.source_id for item in first}
    reordered_ids = {item.title: item.source_id for item in reordered}
    assert first_ids["选校"] == reordered_ids["选校"]
    assert first_ids["文书"] == reordered_ids["文书"]


def test_delimiter_keeps_first_segment_and_long_ids_are_unique() -> None:
    segments = split_transcript(
        "第一段内容\n---CUT---\n第二段内容",
        namespace="batch",
        delimiter="---CUT---",
    )
    assert [item.body for item in segments] == ["第一段内容", "第二段内容"]

    prefix = "这是一个非常长的相同标题前缀" * 8
    segments = split_transcript(f"# {prefix}甲\n\n甲\n# {prefix}乙\n\n乙", namespace="batch")
    assert len({item.source_id for item in segments}) == 2


def test_reimport_removes_deleted_batch_sources(knowledge_vault: Path, tmp_path: Path) -> None:
    merged = tmp_path / "merged.md"
    merged.write_text("# 第一\n\n内容一\n# 第二\n\n内容二\n", encoding="utf-8")
    index = KnowledgeIndex(knowledge_vault)
    try:
        index.import_transcript(merged, batch_id="replaceable")
        index.index_sources()
        assert index.search("内容二")
        merged.write_text("# 第一\n\n内容一\n", encoding="utf-8")
        index.import_transcript(merged, batch_id="replaceable")
        index.index_sources()
        assert not any(result.source_id.endswith("-第二") for result in index.search("内容二"))
    finally:
        index.close()


    merged = tmp_path / "merged.md"
    merged.write_text("# 如何选校\n\n选校要看匹配，不只看排名。\n\n# 文书场景\n\n文书需要具体场景。\n", encoding="utf-8")
    index = KnowledgeIndex(knowledge_vault)
    try:
        index.import_transcript(merged, advisor="测试顾问", batch_id="advisor-a")
        assert index.index_sources() == 2
        results = index.search("选校匹配")
        assert results
        assert "选校" in results[0].content
        assert results[0].citation.startswith("src-advisor-a-如何选校#")
    finally:
        index.close()


def test_old_cache_schema_is_rebuilt(knowledge_vault: Path) -> None:
    db_path = knowledge_vault / ".brain/knowledge.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE sources(source_id TEXT PRIMARY KEY)")
    connection.commit()
    connection.close()
    index = KnowledgeIndex(knowledge_vault)
    try:
        columns = {row[1] for row in index.connection.execute("PRAGMA table_info(sources)")}
        assert "source_revision" in columns
    finally:
        index.close()


def test_remote_embedding_requires_explicit_consent(knowledge_vault: Path, tmp_path: Path) -> None:
    merged = tmp_path / "merged.md"
    merged.write_text("# 选校\n\n看匹配。\n", encoding="utf-8")
    fake = FakeEmbeddingClient()
    index = KnowledgeIndex(knowledge_vault)
    try:
        index.import_transcript(merged, batch_id="private")
        index.index_sources(embed_client=fake)
        index.search("选校", embed_client=fake)
        assert fake.calls == []
    finally:
        index.close()


def test_embedding_index_is_incremental(knowledge_vault: Path, tmp_path: Path) -> None:
    merged = tmp_path / "merged.md"
    merged.write_text("# 选校\n\n看匹配。\n", encoding="utf-8")
    fake = FakeEmbeddingClient()
    index = KnowledgeIndex(knowledge_vault)
    try:
        index.import_transcript(merged, batch_id="batch-a")
        assert index.index_sources(embed_client=fake, allow_remote_content=True) == 1
        assert len(fake.calls) == 1
        assert index.index_sources(embed_client=fake) == 0
        assert len(fake.calls) == 1
    finally:
        index.close()


def test_vector_search_can_retrieve_semantic_match(knowledge_vault: Path, tmp_path: Path) -> None:
    merged = tmp_path / "merged.md"
    merged.write_text("# 文书\n\n文书需要具体场景。\n# 选校\n\n选择学校要考虑环境。\n", encoding="utf-8")
    fake = FakeEmbeddingClient()
    index = KnowledgeIndex(knowledge_vault)
    try:
        index.import_transcript(merged, batch_id="batch-b")
        index.index_sources(embed_client=fake, allow_remote_content=True)
        results = index.search("如何写文书", embed_client=fake, allow_remote_query=True)
        assert results[0].match_type in {"关键词+向量", "向量"}
        assert "文书" in results[0].content
    finally:
        index.close()
