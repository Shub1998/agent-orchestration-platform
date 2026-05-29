import os
import uuid
from app.config import settings


class MemoryManager:
    """Manages per-agent vector memory using ChromaDB."""

    def __init__(self):
        self._client = None
        self._collections: dict = {}

    def _get_client(self):
        if self._client is None:
            import chromadb
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        return self._client

    def _get_collection(self, agent_id: str):
        if agent_id not in self._collections:
            client = self._get_client()
            self._collections[agent_id] = client.get_or_create_collection(
                name=f"agent_{agent_id.replace('-', '_')}",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[agent_id]

    def store(self, agent_id: str, input_text: str, output_text: str, execution_id: str = None) -> str:
        try:
            collection = self._get_collection(agent_id)
            doc_id = str(uuid.uuid4())
            document = f"Input: {input_text}\nOutput: {output_text}"
            collection.add(
                documents=[document],
                ids=[doc_id],
                metadatas=[{"agent_id": agent_id, "execution_id": execution_id or ""}],
            )
            return doc_id
        except Exception:
            return ""

    def retrieve(self, agent_id: str, query: str, k: int = 5) -> str:
        try:
            collection = self._get_collection(agent_id)
            if collection.count() == 0:
                return ""
            results = collection.query(query_texts=[query], n_results=min(k, collection.count()))
            docs = results.get("documents", [[]])[0]
            if not docs:
                return ""
            return "\n---\n".join(docs)
        except Exception:
            return ""

    def clear(self, agent_id: str):
        try:
            client = self._get_client()
            collection_name = f"agent_{agent_id.replace('-', '_')}"
            client.delete_collection(collection_name)
            self._collections.pop(agent_id, None)
        except Exception:
            pass


memory_manager = MemoryManager()
