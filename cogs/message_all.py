import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import ButtonStyle, Interaction
from datetime import datetime, timedelta


class MessageAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    @commands.hybrid_command(name="message_all", description="Send a message to everyone in the server.")
    @commands.has_permissions(administrator=True)
    async def message_all(self, ctx, title: str, content: str, footer: str, color: str = "#3498db"):
        user_id = ctx.author.id
        excluded_ids = [830556605116448779, 1033834366822002769]  # List of IDs exempt from cooldown
        cooldown_time = timedelta(hours=1)

        # Cooldown check
        if user_id not in excluded_ids:
            if user_id in self.cooldowns and datetime.now() - self.cooldowns[user_id] < cooldown_time:
                time_remaining = cooldown_time - (datetime.now() - self.cooldowns[user_id])
                await ctx.send(f"❌ You must wait {time_remaining} before using this command again.")
                return

        # Create the embed
        embed = self.create_embed(title, content, footer, color)

        # Create the buttons
        buttons = self.create_buttons(ctx, embed)

        # Send the preview
        preview_msg = await ctx.send(
            embed=embed,
            content="**Preview**: Adjust before sending:",
            view=buttons,
            ephemeral=True
        )

        # Save necessary data for callbacks
        buttons.preview_msg = preview_msg
        buttons.embed = embed
        buttons.user_id = user_id
        buttons.cooldowns = self.cooldowns

    def create_embed(self, title: str, content: str, footer: str, color: str):
        """Creates a Discord embed with the provided parameters."""
        try:
            embed_color = int(color.strip("#"), 16)
        except ValueError:
            embed_color = 0x3498db  # Default color if invalid
        embed = discord.Embed(title=title, description=content, color=embed_color)
        embed.set_footer(text=footer)
        return embed

    def create_buttons(self, ctx, embed):
        """Creates and configures interaction buttons."""
        buttons = View(timeout=300)  # Timeout of 5 minutes

        confirm_button = Button(label="Confirm", style=ButtonStyle.green)
        cancel_button = Button(label="Cancel", style=ButtonStyle.red)
        edit_button = Button(label="Edit", style=ButtonStyle.blurple)
        color_button = Button(label="Change Color", style=ButtonStyle.grey)

        # Callbacks for each button
        async def confirm_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ You cannot confirm this action.", ephemeral=True)
                return
            failed_members = await self.send_to_all_members(ctx.guild, embed)
            self.cooldowns[ctx.author.id] = datetime.now()
            await interaction.response.edit_message(content=f"✅ Message successfully sent.\n{failed_members} members were unreachable.", view=None)

        async def cancel_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ You cannot cancel this action.", ephemeral=True)
                return
            await interaction.response.edit_message(content="❌ Sending canceled.", view=None)

        async def edit_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ You cannot edit this message.", ephemeral=True)
                return
            await self.handle_edit(interaction, embed)

        async def color_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ You cannot edit this message.", ephemeral=True)
                return
            await self.handle_color_change(interaction, embed)

        # Assign callbacks
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        edit_button.callback = edit_callback
        color_button.callback = color_callback

        # Add buttons to the view
        buttons.add_item(confirm_button)
        buttons.add_item(cancel_button)
        buttons.add_item(edit_button)
        buttons.add_item(color_button)

        return buttons

    async def send_to_all_members(self, guild, embed):
        """Sends the message to all members of the server."""
        failed_members = []
        for member in guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    continue
                except Exception:
                    failed_members.append(str(member))
        return len(failed_members)

    async def handle_edit(self, interaction, embed):
        """Allows the user to edit the fields of the embed."""
        await interaction.response.send_message("📝 Enter the fields to edit (`title`, `content`, `footer`).", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        msg = await self.bot.wait_for('message', check=check)
        fields_to_edit = msg.content.split()
        for field in fields_to_edit:
            if field == "title":
                await interaction.followup.send("Enter the new title:", ephemeral=True)
                title_msg = await self.bot.wait_for('message', check=check)
                embed.title = title_msg.content
            elif field == "content":
                await interaction.followup.send("Enter the new content:", ephemeral=True)
                content_msg = await self.bot.wait_for('message', check=check)
                embed.description = content_msg.content
            elif field == "footer":
                await interaction.followup.send("Enter the new footer:", ephemeral=True)
                footer_msg = await self.bot.wait_for('message', check=check)
                embed.set_footer(text=footer_msg.content)
        await interaction.edit_original_response(embed=embed)

    async def handle_color_change(self, interaction, embed):
        """Allows the user to change the color of the embed."""
        await interaction.response.send_message("🎨 Enter a new color in hexadecimal format.", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        color_msg = await self.bot.wait_for('message', check=check)
        try:
            embed.color = int(color_msg.content.strip("#"), 16)
            await interaction.edit_original_response(embed=embed)
        except ValueError:
            await interaction.followup.send("❌ Invalid color.", ephemeral=True)

# Add the cog
async def setup(bot):
    await bot.add_cog(MessageAll(bot))