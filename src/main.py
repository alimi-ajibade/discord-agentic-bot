import asyncio
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from loguru import logger
from src.core.config import settings
from src.core.bot import bot

from src import event, command

@asynccontextmanager
async def lifespan(app: FastAPI):
    token = settings.DISCORD_TOKEN
    if token:
        # Start the bot in the background without awaiting
        logger.info("Starting Discord bot...")
        bot_task = asyncio.create_task(bot.start(token))
    else:
        logger.error("DISCORD_BOT_TOKEN not found")
    
    yield
    
    # Clean up on shutdown
    if 'bot_task' in locals() and not bot_task.done():
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
