from discord import ChannelType
from sqlalchemy import select

from src.bot.bot import bot
from src.core.database import AsyncSessionLocal
from src.core.logging import logger
from src.models import Channel, Guild


@bot.event
async def on_guild_join(guild):
    """Sends a message to the system channel when the bot joins a new server."""
    logger.info(f'Joined server: {guild.name} (ID: {guild.id})')

    # logger.info(f'Channels in {guild.name}:')
    # for channel in guild.channels:
    #     logger.info(f'  - {channel.name} (ID: {channel.id}, Type: {channel.type})')

    # Save guild and text channels to database
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Guild).where(Guild.discord_guild_id == str(guild.id))
            )
            existing_guild = result.scalar_one_or_none()

            if existing_guild:
                logger.info(f'Guild {guild.name} already exists in database')
                db_guild = existing_guild
            else:
                db_guild = Guild(
                    discord_guild_id=str(guild.id),
                    name=guild.name
                )
                session.add(db_guild)
                await session.commit()
                await session.refresh(db_guild)
                logger.info(f'Created guild {guild.name} in database')

            text_channels = [c for c in guild.channels if c.type == ChannelType.text]
            for channel in text_channels:
                result = await session.execute(
                    select(Channel).where(Channel.discord_channel_id == str(channel.id))
                )
                existing_channel = result.scalar_one_or_none()

                if existing_channel:
                    logger.info(f'Channel {channel.name} already exists in database')
                    continue

                # Create channel
                db_channel = Channel(
                    discord_channel_id=str(channel.id),
                    name=channel.name,
                    guild_id=db_guild.id,
                )
                session.add(db_channel)
                logger.info(f'Created channel {channel.name} in database')

            await session.commit()
            logger.info('Successfully saved guild and text channels to database')

        except Exception as e:
            await session.rollback()
            logger.error(f'Error saving guild and channels to database: {e}')
            raise

