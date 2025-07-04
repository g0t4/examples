from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

chunks = [
    "Reads a file line by line in Python",
    "Sends an HTTP request using the requests library",
    "Calculates the square root of a number",
    "Handles file input and output",
    
]

query = "How do I open a file and read its contents?"

model = SentenceTransformer("all-MiniLM-L6-v2")

chunk_embeddings = model.encode(chunks)
query_embedding = model.encode([query])

scores = cosine_similarity(query_embedding, chunk_embeddings)[0]

# Find the top match
best_idx = int(np.argmax(scores))
best_chunk = chunks[best_idx]
best_score = scores[best_idx]

print(f"Query: {query}")
print(f"Top match: {best_chunk}")
print(f"Similarity: {best_score:.3f}")

# # Assert something if testing
# assert best_score > 0.5  # Can tweak this threshold

