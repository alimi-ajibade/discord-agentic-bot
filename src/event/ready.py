
from src.core.bot import bot
from loguru import logger

@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')



    