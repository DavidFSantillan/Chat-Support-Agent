from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

async def get_embedding(text: str) -> list[float]:
    """Get the embedding vector for the given text using  API"""

    text = text.replace("\n", " ").strip()

    response = await client.embeddings.create(
        input=text,
        model=settings.embedding_model_name,
    )
    embedding = response.data[0].embedding
    return embedding

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embedding vectors for a batch of texts using  API"""

    cleaned_texts = [text.replace("\n", " ").strip() for text in texts]

    response = await client.embeddings.create(
        input=cleaned_texts,
        model=settings.embedding_model_name,
    )
    embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    return embeddings