from discord.ext import commands
from discord import Embed, Color, Interaction, SelectOption
from discord.ui import View, Select
import discord
from datetime import datetime, timedelta
import asyncio

class InfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="infos", description="Get information about the bot and its commands.")
    async def infos(self, ctx: commands.Context):
        # Check permissions: the user must have the 'Manage Messages' permission
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ You do not have permission to use this command.")
            return

        # Create the base embed
        embed = discord.Embed(
            title="Bot Information",
            description="I am the official bot of Monios C., here is some information about me. \nNote that all the following commands are more accessible and smoother with '/'",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Creator", value="@.Calbusto (ID: 1033834366822002769)", inline=False)
        embed.add_field(name="Bot Creation Date", value="May 5, 2025 (V1)", inline=False)
        embed.add_field(name="Select a Command", value="Use the dropdown menu below to get information about a command.", inline=False)

        # Create the dropdown selector to choose a command
        select = Select(
            placeholder="Choose a command for more information",
            options=[
                discord.SelectOption(label="!send", description="Send a message as the bot.", value="say"),
                discord.SelectOption(label="!ban", description="Ban a member", value="ban"),
                discord.SelectOption(label="!unban", description="Unban a member", value="unban"),
                discord.SelectOption(label="!mute", description="Mute a member", value="mute"),
                discord.SelectOption(label="!unmute", description="Unmute a member", value="unmute"),
                discord.SelectOption(label="!kick", description="Kick a member", value="kick"),
                discord.SelectOption(label="!message_all", description="Send a message to all members", value="message_all"),
                discord.SelectOption(label="!send", description="Send a message as the bot", value="send"),
                discord.SelectOption(label="!send_temp", description="Send a temporary message as the bot", value="send_temp"),
                discord.SelectOption(label="!dm", description="Send a private message to a member", value="dm"),
                discord.SelectOption(label="!dm_embed", description="Send a private embed message to a member", value="dm_embed"),
                discord.SelectOption(label="!reset", description="Reset a channel", value="reset"),
                discord.SelectOption(label="!automod", description="Enable auto-moderation for words in the server", value="automod_enable/disable"),
            ]
        )

        # Response function for the dropdown selector
        async def select_callback(interaction: discord.Interaction):
            selected_value = select.values[0]
            
            if selected_value == "automod_enable/disable":
                info_embed = discord.Embed(
                    title="Command !automod_enable/disable (alias: !atm_e/d)",
                    description="This command enables auto-moderation on the server.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="!automod_enable/disable", inline=False)
                info_embed.add_field(name="Example", value="!automod_enable or automod_disable", inline=False)
                info_embed.add_field(name="Required Permission", value="Administrator", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="None.", inline=False)
                
            if selected_value == "send":
                info_embed = discord.Embed(
                    title="Command !send",
                    description="This command allows you to send a message as the bot.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="!send ['message']", inline=False)
                info_embed.add_field(name="Example", value="!send 'Hello, this is the bot'", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Channels", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="None", inline=False)
                
            if selected_value == "send_temp":
                info_embed = discord.Embed(
                    title="Command !send_temp (alias: !st)",
                    description="This command allows you to send a temporary message as the bot.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="!send_temp ['message'] [time]", inline=False)
                info_embed.add_field(name="Example", value="!send_temp/st 'Hello, this is the bot' 10d/10h/10m/10s", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Channels", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="None", inline=False)
            
            if selected_value == "ban":
                info_embed = discord.Embed(
                    title="Command !ban",
                    description="This command allows you to ban a member from the server.",
                    color=discord.Color.red()
                )
                info_embed.add_field(name="Usage", value="!ban [member] [reason]", inline=False)
                info_embed.add_field(name="Example", value="!ban @user Spam", inline=False)
                info_embed.add_field(name="Required Permission", value="Administrator or Manage Members", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="!kick.", inline=False)

            elif selected_value == "unban":
                info_embed = discord.Embed(
                    title="Command !unban",
                    description="This command allows you to unban a member from the server.",
                    color=discord.Color.green()
                )
                info_embed.add_field(name="Usage", value="!unban [Member ID]", inline=False)
                info_embed.add_field(name="Example", value="!unban 123456789012345678", inline=False)
                info_embed.add_field(name="Required Permission", value="Administrator", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="None.", inline=False)

            elif selected_value == "mute":
                info_embed = discord.Embed(
                    title="Command !mute",
                    description="This command allows you to mute a member for a specified duration.",
                    color=discord.Color.orange()
                )
                info_embed.add_field(name="Usage", value="!mute [member] [duration] [reason]", inline=False)
                info_embed.add_field(name="Example", value="!mute @user 10 Spam", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Members", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="!jail", inline=False)

            elif selected_value == "unmute":
                info_embed = discord.Embed(
                    title="Command !unmute",
                    description="This command allows you to unmute a member.",
                    color=discord.Color.blue())
                info_embed.add_field(name="Usage", value="!unmute [member]", inline=False)
                info_embed.add_field(name="Example", value="!unmute @user", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Members", inline=False)
                info_embed.add_field(name="Other Similar Commands", value="None.", inline=False)

            elif selected_value == "kick":
                info_embed = discord.Embed(
                    title="Command !kick",
                    description="This command allows you to kick a member from the server.",
                    color=discord.Color.purple()
                )
                info_embed.add_field(name="Usage", value="!kick [member] [reason]", inline=False)
                info_embed.add_field(name="Example", value="!kick @user Inappropriate behavior", inline=False)
                info_embed.add_field(name="Required Permission", value="Administrator", inline=False)

            elif selected_value == "message_all":
                info_embed = discord.Embed(
                    title="Command !message_all",
                    description="This command allows you to send a message to all members of the server.",
                    color=discord.Color.blue()
                )
                info_embed.add_field(name="Usage", value="!message_all [message]", inline=False)
                info_embed.add_field(name="Example", value="!message_all Attention everyone!", inline=False)
                info_embed.add_field(name="Required Permission", value="Administrator with Manage Server permission", inline=False)

            elif selected_value == "dm":
                info_embed = discord.Embed(
                    title="Command !dm",
                    description="This command allows you to send a private message to a mentioned member.",
                    color=discord.Color.purple()
                )
                info_embed.add_field(name="Usage", value="!dm [member] [message]", inline=False)
                info_embed.add_field(name="Example", value="!dm @user Hi!", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Messages", inline=False)

            elif selected_value == "dm_embed":
                            info_embed = discord.Embed(
                                title="Command !dm_embed",
                                description="TThis command allows you to send a private message to a user. The message will be sent as an embed.",
                                color=discord.Color.purple()
                            )
                            info_embed.add_field(name="Usage", value="!dm_embed [title] [description] [body] [footer] [color]", inline=False)
                            info_embed.add_field(name="Example", value="!dm_embed @user 'Important !' '- Vous êtes accepté dans le staff.' 'votre candidature a été retenue, lu et apprécié par le staff, tout d'abord.." 'le staff' 'FFFFFF', inline=False)
                            info_embed.add_field(name="Required Permission", value="Manage Messages", inline=False)

            elif selected_value == "reset":
                info_embed = discord.Embed(
                    title="Command !reset",
                    description="This command allows you to reset a channel by deleting all messages.",
                    color=discord.Color.dark_gray()
                )
                info_embed.add_field(name="Usage", value="!reset [channel]", inline=False)
                info_embed.add_field(name="Example", value="!reset #channel", inline=False)
                info_embed.add_field(name="Required Permission", value="Manage Messages", inline=False)

            await interaction.response.edit_message(embed=info_embed, view=view)

        select.callback = select_callback

        # Create the view with the dropdown selector
        view = View()
        view.add_item(select)

        # Send the initial embed with the dropdown selector
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(InfoCommand(bot))