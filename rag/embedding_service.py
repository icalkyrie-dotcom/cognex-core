import os
from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        pass


class SentenceTransformerProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.dimension = 384

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        self.dimension = 1536

    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]

    def embed_single(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=[text],
            model=self.model_name
        )
        return response.data[0].embedding


def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    return SentenceTransformerProvider()


# Singleton — load model sekali, reuse
_provider = None

def get_provider() -> BaseEmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = get_embedding_provider()
    return _provider