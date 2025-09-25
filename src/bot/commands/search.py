from discord.ext.commands import Context

from src.bot.bot import bot


@bot.command()
async def search(ctx: Context, *, query: str):
    """Search command that responds with the search query."""
    await ctx.send(
        f'The command is currently under development 🛠️.\nYour query was "{query}".'
    )
