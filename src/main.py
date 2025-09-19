import asyncio

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from src.bot import commands, events, bot  # noqa: F401
from src.core.config import settings
from src.core.logging import logger
from src.utils.embedding import generate_embeddings


@asynccontextmanager
async def lifespan(app: FastAPI):
    token = settings.DISCORD_TOKEN
    if token:
        # Start the bot in the background without awaiting
        logger.info("Starting Discord bot...")
        bot_task = asyncio.create_task(bot.start(token))

        global embedding_task
        embedding_task = asyncio.create_task(generate_embeddings(batch_size=50))
    else:
        logger.error("DISCORD_BOT_TOKEN not found")

    yield

    # Clean up on shutdown
    if embedding_task:
        embedding_task.cancel()
        try:
            await embedding_task
        except asyncio.CancelledError:
            pass

    if "bot_task" in locals() and not bot_task.done():
        await bot.close()
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Discord Agentic Bot",
    description="Discord Agentic Bot",
    version="0.0.1",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
