import json
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.app.config import settings


class DocumentStore:
    def __init__(self, metadata_path: Optional[Path] = None):
        self.metadata_path = metadata_path or (settings.DOC_STORE_PATH / "metadata.json")
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        with self._lock:
            if self.metadata_path.exists():
                try:
                    with open(self.metadata_path, "r", encoding="utf-8") as f:
                        self._store = json.load(f)
                except Exception:
                    self._store = {}
            else:
                self._store = {}

    def _save(self):
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._store, f, indent=2)

    def add_document(self, doc_data: Dict[str, Any]):
        with self._lock:
            self._store[doc_data["id"]] = doc_data
            self._save()

    def update_status(self, doc_id: str, status: str, chunks_count: int = 0, error: Optional[str] = None):
        with self._lock:
            if doc_id in self._store:
                self._store[doc_id]["status"] = status
                if chunks_count:
                    self._store[doc_id]["chunks_count"] = chunks_count
                if error:
                    self._store[doc_id]["error"] = error
                self._save()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(doc_id)

    def get_document_by_sha256(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for doc in self._store.values():
                if doc.get("sha256") == sha256_hash:
                    return doc
            return None

    def list_documents(self, ready_only: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            docs = list(self._store.values())
            if ready_only:
                docs = [d for d in docs if d.get("status") == "ready"]
            return docs


document_store = DocumentStore()
