import asyncio

from google import genai
from google.genai.types import ContentEmbedding, EmbedContentConfig
from sqlalchemy import select

from src.core import logger
from src.core.database import AsyncSessionLocal
from src.models import Message

client = genai.Client()


def get_embedding(text: str) -> ContentEmbedding | None:
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=genai.types.EmbedContentConfig(output_dimensionality=768),
        )

        [embedding_obj] = result.embeddings
        # embedding_length = len(embedding_obj.values)

        return embedding_obj

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


async def get_embeddings_batch(
    texts: list[str], sleep_between_requests: float = 0.0
) -> list[list[float]]:
    embeddings = []

    for text in texts:
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=EmbedContentConfig(output_dimensionality=768),
            )
            # Usually a single embedding per text
            [embedding_obj] = result.embeddings
            embeddings.append(embedding_obj.values)

        except Exception as e:
            logger.error(f"Error generating embedding for text: {text[:50]}... | {e}")
            embeddings.append([])

        if sleep_between_requests > 0:
            await asyncio.sleep(sleep_between_requests)
        else:
            await asyncio.sleep(0)

    return embeddings


async def generate_embeddings(batch_size: int = 50, sleep_seconds: int = 5) -> None:
    while True:
        async with AsyncSessionLocal.begin() as session:
            # Fetch messages without embeddings
            result = await session.execute(
                select(Message).where(Message.embedding.is_(None)).limit(batch_size)  # noqa: E711
            )
            messages_to_embed = result.scalars().all()

            if not messages_to_embed:
                await asyncio.sleep(sleep_seconds)
                continue

            # Extract message content
            texts = [msg.content for msg in messages_to_embed]

            # Generate embeddings in batch
            vectors = await get_embeddings_batch(texts)

            # Update messages
            for msg, vec in zip(messages_to_embed, vectors):
                msg.embedding = vec  # type: ignore

            logger.info(f"Embedded {len(messages_to_embed)} messages in this batch.")


async def find_similar_messages(query: str, top_k: int = 5) -> list[Message]:
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.embedding.is_not(None))
            .order_by(Message.embedding.cosine_distance(query_embedding.values))
            .limit(top_k)
        )
        similar_messages = result.scalars().all()
        logger.info(f"Found {len(similar_messages)} similar messages:")
        for i, msg in enumerate(similar_messages, start=1):
            logger.info(f"  {i}. {msg.content}")
        return similar_messages
