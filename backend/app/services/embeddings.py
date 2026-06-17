import voyageai
from app.config import settings

_vo: voyageai.Client | None = None


def get_embed_client() -> voyageai.Client:
    global _vo
    if _vo is None:
        _vo = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
    return _vo


def embed_text(text: str, model: str | None = None) -> list[float]:
    client = get_embed_client()
    result = client.embed(
        texts=[text],
        model=model or settings.VOYAGE_EMBED_MODEL,
        input_type="document",
    )
    return result.embeddings[0]


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    client = get_embed_client()
    result = client.embed(
        texts=texts,
        model=model or settings.VOYAGE_EMBED_MODEL,
        input_type="document",
    )
    return result.embeddings
