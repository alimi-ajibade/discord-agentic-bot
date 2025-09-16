from src.bot.bot import bot
from src.core import logger


@bot.command()
async def instruction(ctx, *, prompt: str):
    """Instruction command that echoes the prompt."""
    if ctx.author != ctx.guild.owner:
        await ctx.send("You are not authorized to use this command 😒.")
        try:
            await ctx.guild.owner.send(
                f"Unauthorized attempt to use the instruction command by {ctx.author.mention} in {ctx.guild.name}."
            )
        except Exception as e:
            logger.error("Error sending DM to guild owner: {}", e)
        return

    await ctx.send(
        f'The command is currently under development 🛠️.\nYour prompt was "{prompt}".'
    )
