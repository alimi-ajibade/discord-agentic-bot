from bot.bot import bot


@bot.command()
async def search(ctx, *, query: str):
    """Search command that responds with the search query."""
    await ctx.send(
        f'The command is currently under development 🛠️.\nYour query was "{query}".'
    )
