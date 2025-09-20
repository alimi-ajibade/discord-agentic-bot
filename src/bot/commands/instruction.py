from sqlalchemy import select

from src.bot.bot import bot
from src.core import logger
from src.core.database import AsyncSessionLocal
from src.models import Agent, Channel


@bot.command()
async def instruction(ctx, *, prompt: str):
    """Instruction command that sets or updates agent instructions for this channel."""
    if ctx.author != ctx.guild.owner:
        await ctx.send(
            f'{ctx.author.mention}, you are not authorized to use this command 😒.'
        )
        try:
            await ctx.guild.owner.send(
                f"Unauthorized attempt to use the instruction command by {ctx.author.mention} in {ctx.guild.name}."
            )
        except Exception as e:
            logger.error("Error sending DM to guild owner: {}", e)
        return

    # Get channel from database
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Channel).where(Channel.discord_channel_id == str(ctx.channel.id))
            )
            db_channel = result.scalar_one_or_none()

            if not db_channel:
                await ctx.send("❌ Channel not found in database. Please make sure the bot has joined this server properly.")
                return

            # Check if channel already has an agent
            if db_channel.agent_id:
                # Update existing agent's instruction
                result = await session.execute(
                    select(Agent).where(Agent.id == db_channel.agent_id)
                )
                db_agent = result.scalar_one_or_none()

                if db_agent:
                    db_agent.instruction = prompt
                    await session.commit()

                    # Send confirmation via DM to guild owner
                    try:
                        await ctx.guild.owner.send(
                            f"✅ **Agent Updated** in {ctx.guild.name} #{ctx.channel.name}\n"
                            f"**New instruction:** {prompt}"
                        )
                        
                        if ctx.message:
                            await ctx.message.delete()
                    except Exception as e:
                        logger.error(f"Error sending DM to guild owner: {e}")
                        await ctx.send("✅ Agent instructions updated! (DM failed - check bot permissions)")

                    logger.info(f"Updated agent {db_agent.id} instruction in channel {ctx.channel.name}")
                else:
                    await ctx.send("❌ Error: Agent reference is invalid. Creating new agent...")
                    db_channel.agent_id = None
                    await session.commit()

            # Create new agent if no existing agent
            if not db_channel.agent_id:
                db_agent = Agent(
                    instruction=prompt,
                    discord_user_id=str(ctx.author.id),
                    guild_id=db_channel.guild_id
                )
                session.add(db_agent)
                await session.commit()
                await session.refresh(db_agent)

                # Update channel with new agent
                db_channel.agent_id = db_agent.id
                await session.commit()

                
                try:
                    await ctx.guild.owner.send(
                        f"✅ **New Agent Created** in {ctx.guild.name} #{ctx.channel.name}\n"
                        f"**Instruction:** {prompt}"
                    )
                    
                    if ctx.message:
                        await ctx.message.delete()
                except Exception as e:
                    logger.error(f"Error sending DM to guild owner: {e}")
                    await ctx.send("✅ New agent created! (DM failed - check bot permissions)")

                logger.info(f"Created new agent {db_agent.id} for channel {ctx.channel.name}")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error managing agent for instruction command: {e}")
            await ctx.send("❌ An error occurred while saving the instruction. Please try again.")
