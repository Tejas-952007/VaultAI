import chromadb
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. SETTINGS
# ============================================================

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "sih_multidocuments"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

STOPWORDS = {
    "what", "are", "is", "the", "a", "an", "we", "should", "for",
    "this", "that", "to", "of", "in", "on", "and", "or", "be",
    "do", "does", "did", "it", "its", "with", "as", "at", "by",
    "from", "was", "were", "will", "would", "can", "could", "our"
}


# ============================================================
# 2. LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("Embedding model loaded.")


# ============================================================
# 3. CONNECT TO CHROMADB
# ============================================================

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(name=COLLECTION_NAME)
print("Connected to collection:", COLLECTION_NAME)
print("Total chunks:", collection.count())


# ============================================================
# 4. LOAD ALL CHUNKS AND METADATA
# ============================================================

data = collection.get(include=["documents", "metadatas"])
documents = data["documents"]
metadatas = data["metadatas"]

print("\nDocuments available:")

pdf_counts = {}
for metadata in metadatas:
    pdf_name = metadata.get("source", "Unknown")
    pdf_counts[pdf_name] = pdf_counts.get(pdf_name, 0) + 1

for pdf_name, count in pdf_counts.items():
    print(f"{pdf_name} -> {count} chunks")


# ============================================================
# 5. PRE-COMPUTE ALL CHUNK EMBEDDINGS ONCE
# ============================================================

print("\nEncoding all chunks (one-time)...")
chunk_embeddings = model.encode(documents, normalize_embeddings=True)
print("Done.")


# ============================================================
# 6. DOCUMENT SELECTION FUNCTION
# ============================================================

def select_document(question):

    print("\n" + "=" * 60)
    print("DOCUMENT SELECTION")
    print("=" * 60)

    print("\nUser Question:")
    print(question)

    question_embedding = model.encode([question], normalize_embeddings=True)

    similarities = cosine_similarity(
        question_embedding,
        chunk_embeddings
    )[0]

    pdf_names = sorted(
        set(metadata.get("source", "Unknown") for metadata in metadatas)
    )

    document_scores = {}

    # Question words used for keyword overlap, with common filler
    # words (the, is, for, what, etc.) removed so they don't
    # artificially inflate the score of documents with more chunks.
    question_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", question.lower())
    ) - STOPWORDS

    for pdf_name in pdf_names:

        pdf_indices = [
            i for i, metadata in enumerate(metadatas)
            if metadata.get("source", "Unknown") == pdf_name
        ]

        pdf_sim_values = [similarities[i] for i in pdf_indices]

        # Z-score normalize each document's own similarities so a
        # bigger chunk count doesn't win just by having more chances
        # at a lucky high score. We measure how UNUSUALLY good the
        # best chunk is relative to that document's own average,
        # not just its raw similarity value.
        doc_mean = float(np.mean(pdf_sim_values))
        doc_std = float(np.std(pdf_sim_values)) or 1e-6

        pdf_similarities_sorted = sorted(pdf_sim_values, reverse=True)
        top_scores = pdf_similarities_sorted[:3]

        raw_semantic_score = float(np.mean(top_scores)) if top_scores else 0.0
        z_semantic_score = (raw_semantic_score - doc_mean) / doc_std

        # Blend: keep raw similarity as the main signal, but let the
        # z-score gently penalize documents whose "best" chunk is only
        # as good as their own average (a sign of generic content).
        semantic_score = raw_semantic_score + (0.02 * z_semantic_score)

        # ---- DEBUG: show what's actually winning this document ----
        best_index = pdf_indices[int(np.argmax(similarities[pdf_indices]))]
        print(f"\n[DEBUG] {pdf_name}")
        print(f"  raw_top3_avg={raw_semantic_score:.4f}  doc_mean={doc_mean:.4f}  z={z_semantic_score:.4f}")
        print(f"  best matching chunk text: {documents[best_index][:200]}")

        keyword_scores = []
        for index in pdf_indices:
            text_words = set(
                re.findall(r"\b[a-zA-Z0-9]+\b", documents[index].lower())
            ) - STOPWORDS

            if question_words:
                overlap = len(question_words & text_words) / len(question_words)
            else:
                overlap = 0.0

            keyword_scores.append(overlap)

        keyword_score = max(keyword_scores) if keyword_scores else 0.0

        phrase_bonus = 0.0
        question_lower = question.lower()

        for index in pdf_indices:
            text = documents[index].lower()

            if "week 1" in question_lower and "week 1" in text:
                phrase_bonus = max(phrase_bonus, 0.30)

            if "environment setup" in question_lower and "environment setup" in text:
                phrase_bonus = max(phrase_bonus, 0.40)

        final_score = (0.50 * semantic_score) + (0.20 * keyword_score) + phrase_bonus
        document_scores[pdf_name] = final_score

    ranked_documents = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)

    print("\nDocument Scores:")
    print("-" * 40)
    for pdf_name, score in ranked_documents:
        print(f"{pdf_name:<40} {score:.4f}")

    top_document, top_score = ranked_documents[0]

    # If there's a clear winner, just use it.
    selected_documents = [top_document]

    # If the #2 document is close behind (ambiguous case), include it
    # too instead of gambling on a single document being right.
    MARGIN = 0.05
    if len(ranked_documents) > 1:
        second_document, second_score = ranked_documents[1]
        if (top_score - second_score) < MARGIN:
            selected_documents.append(second_document)

    print("\n" + "-" * 60)
    if len(selected_documents) == 1:
        print("SELECTED DOCUMENT:")
        print(selected_documents[0])
        print(f"Selection Score: {top_score:.4f}")
    else:
        print("CLOSE SCORES - SEARCHING MULTIPLE DOCUMENTS:")
        for doc in selected_documents:
            print(f"  - {doc} ({document_scores[doc]:.4f})")
    print("-" * 60)

    return selected_documents


# ============================================================
# 7. SOURCE-CONSTRAINED RETRIEVAL
# ============================================================

def retrieve_from_document(question, selected_documents, top_k=5):

    print("\n" + "=" * 60)
    print("SOURCE-CONSTRAINED RETRIEVAL")
    print("=" * 60)

    # Accept either a single PDF name (string) or a list of PDF names.
    if isinstance(selected_documents, str):
        selected_documents = [selected_documents]

    print("\nSearching only:")
    for doc in selected_documents:
        print(f"  - {doc}")

    ranked = []

    if len(selected_documents) == 1:
        selected_indices = [
            i for i, metadata in enumerate(metadatas)
            if metadata.get("source", "Unknown") == selected_documents[0]
        ]
        selected_chunk_embeddings = chunk_embeddings[selected_indices]
        question_embedding = model.encode([question], normalize_embeddings=True)
        similarities = cosine_similarity(question_embedding, selected_chunk_embeddings)[0]
        order = np.argsort(similarities)[::-1]
        k = min(top_k, len(order))
        for position in order[:k]:
            original_index = selected_indices[position]
            ranked.append((original_index, float(similarities[position])))

    else:
        # Guarantee each selected document gets a fair share of the
        # slots instead of letting one document's naturally higher
        # scores crowd out the other document entirely.
        per_doc_k = max(1, top_k // len(selected_documents))
        question_embedding = model.encode([question], normalize_embeddings=True)

        for doc in selected_documents:
            doc_indices = [
                i for i, metadata in enumerate(metadatas)
                if metadata.get("source", "Unknown") == doc
            ]
            doc_embeddings = chunk_embeddings[doc_indices]
            doc_similarities = cosine_similarity(question_embedding, doc_embeddings)[0]
            order = np.argsort(doc_similarities)[::-1]
            k = min(per_doc_k, len(order))
            for position in order[:k]:
                original_index = doc_indices[position]
                ranked.append((original_index, float(doc_similarities[position])))

        # Fill any remaining slots with the next-best chunks overall.
        remaining = top_k - len(ranked)
        if remaining > 0:
            used = {idx for idx, _ in ranked}
            all_indices = [
                i for i, metadata in enumerate(metadatas)
                if metadata.get("source", "Unknown") in selected_documents and i not in used
            ]
            if all_indices:
                all_embeddings = chunk_embeddings[all_indices]
                all_similarities = cosine_similarity(question_embedding, all_embeddings)[0]
                order = np.argsort(all_similarities)[::-1]
                for position in order[:remaining]:
                    original_index = all_indices[position]
                    ranked.append((original_index, float(all_similarities[position])))

        ranked.sort(key=lambda x: x[1], reverse=True)

    results = []
    for original_index, score in ranked:
        results.append({
            "document": documents[original_index],
            "metadata": metadatas[original_index],
            "score": score
        })

    print("\nTop relevant chunks:")
    print("-" * 60)
    for i, result in enumerate(results, start=1):
        source = result["metadata"].get("source", "Unknown")
        print(f"\nResult {i}  [{source}]")
        print(f"Similarity: {result['score']:.4f}")
        print("\nText:")
        print(result["document"][:500])

    return results


# ============================================================
# 8. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT QUESTION ANSWERING")
    print("=" * 60)

    question = input("\nEnter your question: ")

    selected_document = select_document(question)

    results = retrieve_from_document(
        question,
        selected_document,
        top_k=5
    )

    print("\n" + "=" * 60)
    print("RETRIEVED SOURCES")
    print("=" * 60)

    for i, result in enumerate(results, start=1):
        source = result["metadata"].get("source", "Unknown")
        print(f"{i}. {source} (score: {result['score']:.4f})")