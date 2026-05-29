"""Tests for the ChromaDB memory manager (uses ephemeral in-memory client)."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_chroma_client():
    """Patch chromadb.PersistentClient with an ephemeral in-memory client."""
    import chromadb
    client = chromadb.EphemeralClient()
    with patch("app.core.memory_manager.MemoryManager._get_client", return_value=client):
        # Fresh instance so _collections cache is empty
        from app.core.memory_manager import MemoryManager
        mgr = MemoryManager()
        mgr._client = client
        yield mgr


def test_store_and_retrieve(mock_chroma_client):
    mgr = mock_chroma_client
    doc_id = mgr.store("agent-1", "What is AI?", "AI stands for Artificial Intelligence.", "exec-1")
    assert doc_id != ""

    result = mgr.retrieve("agent-1", "What is AI?")
    assert "Artificial Intelligence" in result


def test_retrieve_empty_collection(mock_chroma_client):
    mgr = mock_chroma_client
    result = mgr.retrieve("agent-new", "anything")
    assert result == ""


def test_retrieve_top_k(mock_chroma_client):
    mgr = mock_chroma_client
    for i in range(5):
        mgr.store("agent-2", f"Question {i}", f"Answer {i}", f"exec-{i}")

    result = mgr.retrieve("agent-2", "Question 0", k=2)
    # Should return at most 2 results joined by ---
    parts = result.split("---")
    assert len(parts) <= 2


def test_clear_removes_data(mock_chroma_client):
    mgr = mock_chroma_client
    mgr.store("agent-3", "hello", "world", "exec-x")
    mgr.clear("agent-3")

    # After clear, retrieval should return empty
    result = mgr.retrieve("agent-3", "hello")
    assert result == ""


def test_store_returns_empty_string_on_error(mock_chroma_client):
    mgr = mock_chroma_client
    # Corrupt the collection cache with a bad object
    mgr._collections["bad-agent"] = MagicMock(side_effect=Exception("boom"))
    result = mgr.store("bad-agent", "x", "y")
    assert result == ""
