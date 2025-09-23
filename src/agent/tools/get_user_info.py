import asyncio

import discord
from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools.base import BaseTool


class GetUserInfo(BaseTool):
    name: str = "get_user_info"
    description: str = """Get information about a Discord user.
    Input should be a user mention (@user), user ID, or username."""
    return_direct: bool = False

    message_ctx: DiscordMessageContext | None = None
    command_ctx: DiscordCommandContext | None = None

    def _run(self, user_identifier: str) -> str:
        return asyncio.run(self._arun(user_identifier))

    async def _arun(self, user_identifier: str) -> str:
        """Async version - Get information about a Discord user."""
        try:
            user = None
            guild = None

            # Get guild context
            if self.message_ctx and hasattr(self.message_ctx, "guild"):
                guild = self.message_ctx.guild
            elif self.command_ctx and hasattr(self.command_ctx, "guild"):
                guild = self.command_ctx.guild

            if not guild:
                return "Error: No guild context available"

            # Parse user identifier
            if user_identifier.startswith("<@") and user_identifier.endswith(">"):
                # Handle mentions like <@123456789> or <@!123456789>
                user_id = (
                    user_identifier.replace("<@", "").replace("!", "").replace(">", "")
                )
                if user_id.isdigit():
                    user = guild.get_member(int(user_id))
            elif user_identifier.isdigit():
                # Handle direct user ID
                user = guild.get_member(int(user_identifier))
            else:
                # Handle username or display name
                user = discord.utils.get(guild.members, name=user_identifier)
                if not user:
                    user = discord.utils.get(
                        guild.members, display_name=user_identifier
                    )

            if not user:
                return f"Error: Could not find user '{user_identifier}'"

            # Build user info
            user_info = {
                "username": user.name,
                "display_name": user.display_name,
                "id": user.id,
                "discriminator": (
                    user.discriminator if user.discriminator != "0" else None
                ),
                "bot": user.bot,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "joined_at": (
                    user.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    if user.joined_at
                    else "Unknown"
                ),
                "status": str(user.status),
                "activity": str(user.activity) if user.activity else "None",
                "roles": [role.name for role in user.roles if role.name != "@everyone"],
                "top_role": (
                    user.top_role.name
                    if user.top_role.name != "@everyone"
                    else "No roles"
                ),
                "avatar_url": str(user.avatar.url) if user.avatar else "No avatar",
            }

            info_text = "**User Information:**\n"
            info_text += f"• Username: {user_info['username']}\n"
            if user_info["discriminator"]:
                info_text += f"• Discriminator: #{user_info['discriminator']}\n"
            info_text += f"• Display Name: {user_info['display_name']}\n"
            info_text += f"• ID: {user_info['id']}\n"
            info_text += f"• Bot: {user_info['bot']}\n"
            info_text += f"• Account Created: {user_info['created_at']}\n"
            info_text += f"• Joined Server: {user_info['joined_at']}\n"
            info_text += f"• Status: {user_info['status']}\n"
            info_text += f"• Activity: {user_info['activity']}\n"
            info_text += f"• Top Role: {user_info['top_role']}\n"
            if user_info["roles"]:
                info_text += f"• Roles: {', '.join(user_info['roles'])}"

            return info_text

        except Exception as e:
            return f"Error getting user info: {str(e)}"
