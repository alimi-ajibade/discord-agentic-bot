import asyncio

import discord
from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools.base import BaseTool


class GetChannelInfo(BaseTool):
    name: str = "get_channel_info"
    description: str = """Get information about the current Discord channel or a specific channel.
    Input should be either empty for current channel or a channel ID/name."""
    return_direct: bool = False

    message_ctx: DiscordMessageContext | None = None
    command_ctx: DiscordCommandContext | None = None

    def _run(self, channel_identifier: str = "") -> str:
        return asyncio.run(self._arun(channel_identifier))

    async def _arun(self, channel_identifier: str = "") -> str:
        """Async version - Get information about a Discord channel."""
        try:
            channel = None

            if not channel_identifier:
                # Get current channel
                if self.message_ctx and hasattr(self.message_ctx, "channel"):
                    channel = self.message_ctx.channel
                elif self.command_ctx and hasattr(self.command_ctx, "channel"):
                    channel = self.command_ctx.channel
            else:
                # Try to get channel by ID or name
                if self.message_ctx and hasattr(self.message_ctx, "guild"):
                    guild = self.message_ctx.guild
                    if channel_identifier.isdigit():
                        channel = guild.get_channel(int(channel_identifier))
                    else:
                        channel = discord.utils.get(
                            guild.channels, name=channel_identifier
                        )

            if not channel:
                return "Error: Could not find the specified channel"

            channel_info = {
                "name": channel.name,
                "id": channel.id,
                "type": str(channel.type),
                "position": getattr(channel, "position", "N/A"),
                "category": (
                    channel.category.name if channel.category else "No category"
                ),
                "topic": getattr(channel, "topic", "No topic") or "No topic",
                "nsfw": getattr(channel, "nsfw", False),
                "member_count": (
                    len(channel.members) if hasattr(channel, "members") else "N/A"
                ),
            }

            info_text = "**Channel Information:**\n"
            info_text += f"• Name: #{channel_info['name']}\n"
            info_text += f"• ID: {channel_info['id']}\n"
            info_text += f"• Type: {channel_info['type']}\n"
            info_text += f"• Category: {channel_info['category']}\n"
            info_text += f"• Topic: {channel_info['topic']}\n"
            info_text += f"• NSFW: {channel_info['nsfw']}\n"
            info_text += f"• Members: {channel_info['member_count']}"

            return info_text

        except Exception as e:
            return f"Error getting channel info: {str(e)}"
