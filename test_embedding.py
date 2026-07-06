from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

text = "Project Jarvis adalah AI Assistant pribadi."

embedding = model.encode(text)

print("Embedding berhasil")
print(f"Dimension : {len(embedding)}")
print(f"Sample    : {embedding[:5]}")