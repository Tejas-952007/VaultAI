import chromadb
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from backend.app.config import settings


class VectorStoreManager:
    def __init__(self):
        self._embedding_model: Optional[SentenceTransformer] = None
        self._chroma_client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._embedding_model

    @property
    def collection(self):
        if self._collection is None:
            settings.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
            self._collection = self._chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def add_chunks(
        self,
        chunk_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ):
        if embeddings is None:
            embeddings = self.embed_texts(texts)

        self.collection.add(
            ids=chunk_ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def query(
        self,
        query_text: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embed_texts([query_text])[0]
        
        where_filter = None
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                # Convert cosine distance to similarity score
                similarity = round(1.0 - float(distances[i]), 4)
                formatted.append({
                    "chunk_id": ids[i],
                    "document_id": metas[i].get("document_id", "unknown"),
                    "source": metas[i].get("source", "unknown"),
                    "text": docs[i],
                    "metadata": metas[i],
                    "score": similarity
                })

        return formatted


vector_store = VectorStoreManager()
