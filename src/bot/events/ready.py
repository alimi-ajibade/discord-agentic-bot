from src.bot.bot import bot
from src.core.logging import logger


@bot.event
async def on_ready():
    logger.info(f"We have logged in as {bot.user}")
