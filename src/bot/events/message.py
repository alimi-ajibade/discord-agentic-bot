from discord import Message as DiscordMessageContext
from discord.channel import DMChannel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.agent.factory import create_agent
from src.bot.bot import bot
from src.core.database import AsyncSessionLocal
from src.core.logging import logger
from src.models import Channel, Guild, Message, User


@bot.event
async def on_message(message: DiscordMessageContext):
    try:
        if not message.content.strip():
            await bot.process_commands(message)
            return

        # Only respond when the bot is mentioned
        if bot.user.mentioned_in(message):
            content_without_mention = message.content.replace(
                f"<@{bot.user.id}>", ""
            ).strip()

            if content_without_mention == "":
                await message.channel.send(f"Hello @{message.author.name}!")
                return

            await save_message_to_db(message)

            agent = create_agent(message_ctx=message)
            response = await agent.ainvoke(
                user_request=content_without_mention,
                user_id=str(message.author.id) if message.author else None,
                instruction=await get_admin_instruction(
                    str(message.guild.id), channel_id=str(message.channel.id)
                ),
            )
            logger.debug(f"response: {response}")

            await bot.process_commands(message)
            return

        await save_message_to_db(message)
        await bot.process_commands(message)
    except Exception as e:
        logger.exception(f"Error handling message: {e}")
        # Optionally, send an error message to the channel
        try:
            await message.channel.send(
                "Sorry, an error occurred while processing your message."
            )
        except Exception as send_error:
            logger.exception(f"Error sending error message: {send_error}")


async def get_admin_instruction(guild_id: str, channel_id: str) -> str:
    if not guild_id and not channel_id:
        return ""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Channel)
                .where(
                    Channel.discord_channel_id == channel_id,
                    Channel.guild.has(Guild.discord_guild_id == guild_id),
                )
                .options(selectinload(Channel.agent))
            )
            db_channel = result.scalar_one_or_none()

            if db_channel and db_channel.agent and db_channel.agent.instruction:
                return db_channel.agent.instruction or ""
        except Exception as e:
            logger.exception(
                f"Error retrieving admin instruction for guild {guild_id}: {e}"
            )
    return ""


async def save_message_to_db(message: DiscordMessageContext):
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
