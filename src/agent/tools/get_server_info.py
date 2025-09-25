import asyncio

import discord
from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools.base import BaseTool


class GetServerInfo(BaseTool):
    name: str = "get_server_info"
    description: str = """Get information about the current Discord server/guild.
    No input required - gets info about the current server."""
    return_direct: bool = False

    message_ctx: DiscordMessageContext | None = None
    command_ctx: DiscordCommandContext | None = None

    def _run(self, input_str: str = "") -> str:
        return asyncio.run(self._arun(input_str))

    async def _arun(self, input_str: str = "") -> str:
        """Async version - Get information about the Discord server."""
        try:
            guild = None

            # Get guild context
            if self.message_ctx and hasattr(self.message_ctx, "guild"):
                guild = self.message_ctx.guild
            elif self.command_ctx and hasattr(self.command_ctx, "guild"):
                guild = self.command_ctx.guild

            if not guild:
                return "Error: No guild context available (this might be a DM)"

            # Get server statistics
            text_channels = len(
                [c for c in guild.channels if isinstance(c, discord.TextChannel)]
            )
            voice_channels = len(
                [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
            )
            categories = len(
                [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]
            )

            # Get member statistics
            online_members = len(
                [m for m in guild.members if m.status != discord.Status.offline]
            )
            bot_members = len([m for m in guild.members if m.bot])
            human_members = len([m for m in guild.members if not m.bot])

            # Build server info
            server_info = {
                "name": guild.name,
                "id": guild.id,
                "description": guild.description or "No description",
                "owner": guild.owner.display_name if guild.owner else "Unknown",
                "created_at": guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "member_count": guild.member_count,
                "online_members": online_members,
                "human_members": human_members,
                "bot_members": bot_members,
                "text_channels": text_channels,
                "voice_channels": voice_channels,
                "categories": categories,
                "roles": len(guild.roles) - 1,  # Exclude @everyone
                "emojis": len(guild.emojis),
                "boosts": guild.premium_subscription_count,
                "boost_level": guild.premium_tier,
                "verification_level": str(guild.verification_level),
                "icon_url": str(guild.icon.url) if guild.icon else "No icon",
            }

            info_text = "**Server Information:**\n"
            info_text += f"• Name: {server_info['name']}\n"
            info_text += f"• ID: {server_info['id']}\n"
            info_text += f"• Description: {server_info['description']}\n"
            info_text += f"• Owner: {server_info['owner']}\n"
            info_text += f"• Created: {server_info['created_at']}\n"
            info_text += f"• Members: {server_info['member_count']} ({server_info['online_members']} online)\n"
            info_text += f"• Humans: {server_info['human_members']} | Bots: {server_info['bot_members']}\n"
            info_text += f"• Text Channels: {server_info['text_channels']}\n"
            info_text += f"• Voice Channels: {server_info['voice_channels']}\n"
            info_text += f"• Categories: {server_info['categories']}\n"
            info_text += f"• Roles: {server_info['roles']}\n"
            info_text += f"• Emojis: {server_info['emojis']}\n"
            info_text += f"• Boost Level: {server_info['boost_level']} ({server_info['boosts']} boosts)\n"
            info_text += f"• Verification Level: {server_info['verification_level']}"

            return info_text

        except Exception as e:
            return f"Error getting server info: {str(e)}"
