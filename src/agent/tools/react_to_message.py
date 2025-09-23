import asyncio

import discord
from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools.base import BaseTool


class ReactToMessage(BaseTool):
    name: str = "react_to_message"
    description: str = """Add a reaction emoji to a message.
    Input should be in the format 'emoji:message_id' or just 'emoji' to react to the current message.
    Example: '👍' or '👍:1234567890123456789'"""
    return_direct: bool = False

    message_ctx: DiscordMessageContext | None = None
    command_ctx: DiscordCommandContext | None = None

    def _run(self, reaction_input: str) -> str:
        return asyncio.run(self._arun(reaction_input))

    async def _arun(self, reaction_input: str) -> str:
        """Async version - Add a reaction emoji to a message."""
        try:
            # Parse input
            if ":" in reaction_input:
                emoji, message_id = reaction_input.split(":", 1)
                message_id = message_id.strip()
            else:
                emoji = reaction_input
                message_id = None

            emoji = emoji.strip()

            # Get the target message
            target_message = None

            if message_id:
                # Try to get specific message by ID
                if message_id.isdigit():
                    if self.message_ctx and hasattr(self.message_ctx, "channel"):
                        try:
                            target_message = (
                                await self.message_ctx.channel.fetch_message(
                                    int(message_id)
                                )
                            )
                        except discord.NotFound:
                            return f"Error: Message with ID {message_id} not found"
                    else:
                        return "Error: No channel context to fetch message"
                else:
                    return f"Error: Invalid message ID '{message_id}'"
            else:
                # React to the current message (the one that triggered the bot)
                if self.message_ctx:
                    target_message = self.message_ctx
                elif self.command_ctx and hasattr(self.command_ctx, "message"):
                    target_message = self.command_ctx.message
                else:
                    return "Error: No message context available"

            if not target_message:
                return "Error: Could not find target message"

            # Add the reaction
            await target_message.add_reaction(emoji)

            return f"Successfully reacted with {emoji} to message"

        except discord.HTTPException as e:
            if "Unknown Emoji" in str(e):
                return f"Error: '{emoji}' is not a valid emoji"
            else:
                return f"Error adding reaction: {str(e)}"
        except Exception as e:
            return f"Error adding reaction: {str(e)}"
