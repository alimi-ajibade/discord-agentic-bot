import asyncio

from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools.base import BaseTool


class SendMessage(BaseTool):
    name: str = "send_message"
    description: str = """Send a message to a Discord channel.
    Input should be the message content as a string.
    Use this tool to respond to users or send information to the current channel."""
    return_direct: bool = False

    message_ctx: DiscordMessageContext | None = None
    command_ctx: DiscordCommandContext | None = None

    def _run(self, content: str) -> str:
        return asyncio.run(self._arun(content))

    async def _arun(self, content: str) -> str:
        """Async version - Send a message to the Discord channel."""
        try:
            if self.message_ctx and hasattr(self.message_ctx, "channel"):
                await self.message_ctx.channel.send(content)
                return f"Message sent successfully: {content}"
            elif self.command_ctx and hasattr(self.command_ctx, "send"):
                # Send via command context
                await self.command_ctx.send(content)
                return f"Message sent successfully: {content}"
            else:
                return "Error: No valid Discord context available to send message"
        except Exception as e:
            return f"Error sending message: {str(e)}"
