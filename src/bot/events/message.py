from discord.channel import DMChannel
from sqlalchemy import select

from src.bot.bot import bot
from src.core.database import AsyncSessionLocal
from src.core.logging import logger
from src.models import Channel, Guild, Message, User


@bot.event
async def on_message(message):
    # Only respond when the bot is mentioned
    if bot.user.mentioned_in(message):
        content_without_mention = message.content.replace(
            f"<@{bot.user.id}>", ""
        ).strip()
        if (
            content_without_mention.lower().startswith("hello")
            or content_without_mention == ""
        ):
            await message.channel.send(f"Hello {message.author.name}!")
        else:
            await message.channel.send(f"You mentioned me, {message.author.name}!")

    # Save message to database
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.discord_user_id == str(message.author.id))
            )
            db_user = result.scalar_one_or_none()

            if not db_user:
                db_user = User(
                    discord_user_id=str(message.author.id), username=message.author.name
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"Created user {message.author.name} in database")

            # Skip DM messages - they don't belong to a guild
            if isinstance(message.channel, DMChannel):
                await bot.process_commands(message)
                return

            # Get or create guild
            result = await session.execute(
                select(Guild).where(Guild.discord_guild_id == str(message.guild.id))
            )
            db_guild = result.scalar_one_or_none()

            if not db_guild:
                db_guild = Guild(
                    discord_guild_id=str(message.guild.id), name=message.guild.name
                )
                session.add(db_guild)
                await session.commit()
                await session.refresh(db_guild)
                logger.info(f"Created guild {message.guild.name} in database")

            # Get or create channel
            result = await session.execute(
                select(Channel).where(
                    Channel.discord_channel_id == str(message.channel.id)
                )
            )
            db_channel = result.scalar_one_or_none()

            if not db_channel:
                db_channel = Channel(
                    discord_channel_id=str(message.channel.id),
                    name=message.channel.name,
                    guild_id=db_guild.id,
                )
                session.add(db_channel)
                await session.commit()
                await session.refresh(db_channel)
                logger.info(f"Created channel {message.channel.name} in database")

            # Save message
            db_message = Message(
                discord_message_id=str(message.id),
                discord_user_id=str(message.author.id),
                content=message.content,
                channel_id=db_channel.id,
                user_id=db_user.id,
                embedding=None,
            )
            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)

            logger.info(
                f"Saved message from {message.author.name} in channel {message.channel.name}"
            )

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error saving message to database: {e}")

    await bot.process_commands(message)
