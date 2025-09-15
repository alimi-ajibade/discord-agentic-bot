import discord
from discord.ext import commands

intents = discord.Intents.default()

# permissions to read messages and member info
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)