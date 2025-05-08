import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio

class BumpReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bump_channel_id = None  # ID of the channel where reminders will be sent
        self.bump_waiting = False  # Indicates if the bot is waiting for the /bump command
        self.bump_cooldown = timedelta(hours=2)  # 2-hour cooldown
        self.last_bump_time = None  # Tracks the last time /bump was executed
        self.bump_bot_id = 302050872383242240  # ID of the bot to wait for
        self.allowed_user_id = 1033834366822002769  # User allowed to use the command
        self.ping_role_id = 1328089777660235898  # Role to ping during reminders

    @commands.command(name="bumpremind_set", description="Set the channel for bump reminders.")
    @commands.has_permissions(administrator=True)
    async def bumpremind_set(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel where bump reminders will be sent."""
        if ctx.author.id != self.allowed_user_id and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You don't have permission to use this command.", delete_after=5)
            return

        if channel is None:
            # Use the current channel if no argument is provided
            self.bump_channel_id = ctx.channel.id
            await ctx.message.delete()  # Delete the user's command message
            await ctx.send(f"✅ Bump reminders will now be sent in {ctx.channel.mention}.", delete_after=5)
        else:
            self.bump_channel_id = channel.id
            await ctx.send(f"✅ Bump reminders will now be sent in {channel.mention}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for messages from the bump bot."""
        if message.author.id == self.bump_bot_id and self.bump_channel_id == message.channel.id:
            self.last_bump_time = datetime.now()
            self.bump_waiting = False
            await asyncio.sleep(self.bump_cooldown.total_seconds())
            await self.send_bump_reminder()

    async def send_bump_reminder(self):
        """Sends a bump reminder to the specified channel."""
        if self.bump_channel_id:
            channel = self.bot.get_channel(self.bump_channel_id)
            if channel:
                self.bump_waiting = True
                ping_role = f"<@&{self.ping_role_id}>"
                await channel.send(f"⏰ It's time to `/bump`! {ping_role}")

async def setup(bot):
    await bot.add_cog(BumpReminder(bot))