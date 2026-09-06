from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

#LOADING THE EMBEDDING MODEL
model = SentenceTransformer("all-MiniLM-L6-v2")

#SOME EXAMPLE SENTENCES
sentences = [
    "What is the recommended technology stack?",
    "The recommended stack includes Ollama, LangChain and ChromaDB.",
    "The refinery processes crude oil into useful products."    
]

#CONVERT THE SENTENCES INTO EMBEDDINGS
embeddings = model.encode(sentences)

#USER QUESTION
query = "What does a refinery produce?"

#CONVERTING QUESTION INTO EMBEDDING
query_embedding = model.encode([query])

#CALCULATE SIMILARITY
similarities = cosine_similarity(query_embedding, embeddings)[0]

#SHOWING RESULTS
for i, score in enumerate(similarities):
    print(f"Sentence {i+1}: {score:.4f}")
    print(sentences[i])
    print()
    
#FIND MOST SIMILAR SENTENCE
best_index = similarities.argmax()

print("MOST RELEVANT SENTENCE: ")
print(sentences[best_index])
