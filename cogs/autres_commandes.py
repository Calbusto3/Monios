import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, View, Button, TextInput
import re
import asyncio
from datetime import datetime, timedelta
import random

class OtherCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel_id = 1266457471573168199  # Logs channel ID
        self.allowed_roles = [1266457418561355900, 1266457425335160854]
        self.welcome_channel_id = 1287840591714979984
        self.role_reactions = {}  # {message_id: {"emoji": role_id}}

    @commands.command(name='mp_embed', description="Send a DM with an embed to a member")
    async def mp_embed(self, ctx, member_input: str = None, title: str = None, description: str = None, body: str = None, footer: str = None, color: discord.Color = discord.Color.yellow()):
        """Send a DM with an embed, with preview and error handling."""
        try:
            # Delete the command message after execution
            await ctx.message.delete()

            # Check required fields
            if not member_input:
                await ctx.send("You must mention a member or provide their ID to send a DM.")
                return
            if not title or not description:
                await ctx.send("You must provide a title and a description for the embed.")
                return

            # Identify the member either by mention or ID
            try:
                if member_input.isdigit():
                    member = await ctx.guild.fetch_member(int(member_input))
                else:
                    member = await commands.MemberConverter().convert(ctx, member_input)
            except:
                await ctx.send("The specified member could not be found.")
                return

            # Create the preview embed
            embed_preview = discord.Embed(
                title=title[:256],  # Limit title to 256 characters
                description=description[:4096],  # Limit description to 4096 characters
                color=color
            )
            if footer:
                embed_preview.set_footer(text=footer[:2048])  # Limit footer to 2048 characters
            if body:
                embed_preview.add_field(name="Message", value=body[:1024], inline=False)  # Limit body to 1024 characters

            embed_preview.set_author(name=f"Preview for {ctx.author.display_name}")
            embed_preview.set_footer(text="Press 'Send' to confirm, 'Edit' to adjust, or 'Cancel' to abandon.")

            # Action buttons
            view = View(timeout=None)

            # Button to send the embed
            async def confirm_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    return

                # Send the final message to the member
                try:
                    await member.send(embed=embed_preview)
                    embed_success = discord.Embed(
                        title="✅ Message sent successfully!",
                        color=discord.Color.green()
                    )
                    await interaction.response.edit_message(embed=embed_success, view=None)
                    
                    # Logs
                    logs_channel = self.bot.get_channel(self.logs_channel_id)
                    if logs_channel:
                        log_embed = discord.Embed(
                            title="📩 Message Sent",
                            description=f"**Recipient**: {member.mention}\n**Sender**: {ctx.author.mention}\n**Message**: {embed_preview.title}",
                            color=discord.Color.green()
                        )
                        await logs_channel.send(embed=log_embed)
                except discord.Forbidden:
                    await interaction.response.send_message(f"I couldn't send a DM to {member.mention}.", ephemeral=True)

            confirm_button = Button(label="Send", style=discord.ButtonStyle.success)
            confirm_button.callback = confirm_callback

            # Button to edit
            async def modify_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    return

                # Request direct modification
                await interaction.response.send_message("Send me your new data for the embed in this format:\n`Title | Description | Footer | Color`\nIf you leave a field empty, it will not be modified.", ephemeral=True)

                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                    await msg.delete()  # Delete the message to avoid spam
                    data = msg.content.split('|')
                    if len(data) >= 1 and data[0].strip():
                        embed_preview.title = data[0].strip()[:256]  # Limit to 256 characters
                    if len(data) >= 2 and data[1].strip():
                        embed_preview.description = data[1].strip()
                    if len(data) >= 3 and data[2].strip():
                        embed_preview.set_footer(text=data[2].strip())
                    if len(data) >= 4 and data[3].strip():
                        try:
                            embed_preview.color = discord.Color(int(data[3].strip(), 16))
                        except ValueError:
                            pass

                    await interaction.message.edit(embed=embed_preview)
                    await interaction.response.send_message("Embed updated!", ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.response.send_message("Time expired for modification.", ephemeral=True)

            modify_button = Button(label="Edit", style=discord.ButtonStyle.primary)
            modify_button.callback = modify_callback

            # Button to cancel
            async def cancel_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    return

                # Cancel the send
                embed_cancelled = discord.Embed(
                    title="💡 Embed send cancelled.",
                    color=discord.Color.yellow()
                )
                await interaction.response.edit_message(embed=embed_cancelled, view=None)

                # Logs
                logs_channel = self.bot.get_channel(self.logs_channel_id)
                if logs_channel:
                    log_embed = discord.Embed(
                        title="❌ Send Cancelled",
                        description=f"{ctx.author.mention} cancelled the embed send intended for {member.mention}.",
                        color=discord.Color.yellow()
                    )
                    await logs_channel.send(embed=log_embed)

            cancel_button = Button(label="Cancel", style=discord.ButtonStyle.danger)
            cancel_button.callback = cancel_callback

            # Add buttons to the view
            view.add_item(confirm_button)
            view.add_item(modify_button)
            view.add_item(cancel_button)

            # Send the preview to the user
            await ctx.send(embed=embed_preview, view=view)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.hybrid_command(name='mp', description="Send a DM to a member")
    async def mp(self, ctx, member: discord.Member = None, *, message: str = None):
        """Send a DM to a member (hybrid command)."""
        try:
            # Validate arguments
            if not member:
                await ctx.send("You must mention a member to send a DM.")
                return
            if not message:
                await ctx.send("You must provide a message to send.")
                return

            await member.send(message)
            await ctx.send(f"Message sent to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("I cannot send a message to this member. They may have disabled their DMs.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    # Slash command /say
    @discord.app_commands.command(name="send", description="Send a message as the bot.")
    async def say_slash(self, interaction: discord.Interaction, message: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You do not have permission for this command.", ephemeral=True)
            return
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Message sent successfully!", ephemeral=True)

    # Prefix command +say
    @commands.command(name="send")
    @commands.has_permissions(manage_channels=True)
    async def say_prefix(self, ctx, *, message: str):
        await ctx.channel.send(message)
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.hybrid_command(name="send_temp", aliases=["send_ts"], help="Send a temporary message as the bot.")
    @commands.has_permissions(manage_channels=True)
    async def send_temp(self, ctx: commands.Context, message: str, temp: str):
        match = re.match(r"(\d+)([smhd])$", temp)
        if not match:
            await ctx.reply(
                "❌ Invalid delay format. Use the format `<number><unit>` with: 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days).",
                ephemeral=True,
            )
            return
        time_value, time_unit = int(match.group(1)), match.group(2)
        delay = time_value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[time_unit]
        bot_message = await ctx.channel.send(message)
        await asyncio.sleep(delay)

    # Welcome system --------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Retrieve the welcome channel
        channel = member.guild.get_channel(self.welcome_channel_id)
        if not channel:
            print("Welcome channel not found.")
            return

        # Retrieve invites to determine the inviter
        inviter = None
        try:
            invites_before = await member.guild.invites()
            for invite in invites_before:
                if invite.uses and invite.inviter:
                    inviter = invite.inviter
                    break
        except discord.Forbidden:
            print("Unable to access server invites.")

        # Server statistics
        total_members = len(member.guild.members)

        # Check for milestone members
        special_message = ""
        if total_members % 100 == 0:
            special_message = (
                f"🎊 {member.mention} is our **{total_members}th member**! "
                "Welcome, hero of this event! 🎉 🎈"
            )

        # Build the embed
        embed = discord.Embed(
            title="🎉 Welcome to Monios C.!",
            description=(
                f"Welcome to **{member.guild.name}**, {member.mention}! 🎉\n\n"
                "We are thrilled to have you with us.\n"
                f"We are now **{total_members} members** in the community! 🎊\n\n"
                f"{special_message}"
            ),
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.avatar.url)
        if inviter:
            embed.add_field(
                name="Thanks to an amazing member:",
                value=f"{inviter.mention} invited {member.mention}. You are awesome! 🙌",
                inline=False
            )
        embed.set_footer(text=f"Server: {member.guild.name}")

        # Send the welcome message with mention
        await channel.send(content=f"Welcome {member.mention}! 🎉", embed=embed)

        # Send a private message to the new member
        try:
            dm_embed = discord.Embed(
                title="Welcome to Monios C.! 🎉",
                description=(
                    f"Hi {member.mention}, welcome to **{member.guild.name}**! 🎊\n\n"
                    "We're so excited to have you join our community. Feel free to explore the server, "
                    "engage with others, and have a great time here!\n\n"
                    "If you have any questions, don't hesitate to reach out to the moderators or admins."
                ),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            dm_embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else "")
            dm_embed.set_footer(text="Enjoy your stay!")
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    @app_commands.command(name="rolereact", description="Create a role-reaction message.")
    @commands.has_permissions(manage_channels=True)
    async def rolereact(self, interaction: discord.Interaction, message: str, role: discord.Role, reaction: str):
        # Send the message in the channel
        embed = discord.Embed(
            title="Role Reaction",
            description=message,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="React to get or remove this role.")
        sent_message = await interaction.channel.send(embed=embed)

        # Add the specified reaction
        await sent_message.add_reaction(reaction)

        # Save the message/reaction/role association
        self.role_reactions[sent_message.id] = {"emoji": reaction, "role_id": role.id}

        # Confirmation message in the same channel visible only to the command executor
        await interaction.response.send_message(
            f"Role-reaction created for {role.mention} with {reaction}.", ephemeral=True
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Check if the reaction matches a role-reaction
        message_id = payload.message_id
        if message_id in self.role_reactions:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member is None or member.bot:
                return  # Ignore bots

            reaction_data = self.role_reactions[message_id]
            if str(payload.emoji) == reaction_data["emoji"]:
                role = guild.get_role(reaction_data["role_id"])
                if role:
                    await member.add_roles(role, reason="Role-reaction added")
                    # Confirmation message in the same channel
                    channel = guild.get_channel(payload.channel_id)
                    await channel.send(f"{member.mention} has been given the role {role.mention}.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Check if the reaction matches a role-reaction
        message_id = payload.message_id
        if message_id in self.role_reactions:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member is None or member.bot:
                return  # Ignore bots

            reaction_data = self.role_reactions[message_id]
            if str(payload.emoji) == reaction_data["emoji"]:
                role = guild.get_role(reaction_data["role_id"])
                if role:
                    await member.remove_roles(role, reason="Role-reaction removed")
                    # Confirmation message in the same channel
                    channel = guild.get_channel(payload.channel_id)
                    await channel.send(f"{member.mention} has removed the role {role.mention}.")
     
async def setup(bot):
    await bot.add_cog(OtherCommands(bot))