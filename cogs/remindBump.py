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

    @commands.command(name="set_bump_channel", description="Set the channel for bump reminders.")
    @commands.has_permissions(administrator=True)
    async def set_bump_channel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel where bump reminders will be sent."""
        if channel is None:
            await ctx.send("❌ Please mention a valid text channel. Example: `!set_bump_channel #general`")
            return

        self.bump_channel_id = channel.id
        await ctx.send(f"✅ Bump reminders will now be sent in {channel.mention}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for the /bump command from the other bot."""
        if message.author.bot and message.content.startswith("/bump"):
            if self.bump_channel_id and message.channel.id == self.bump_channel_id:
                self.last_bump_time = datetime.now()
                self.bump_waiting = False
                await message.channel.send(f"✅ Thank you for the bump {message.author.mention} !")
                await asyncio.sleep(self.bump_cooldown.total_seconds())
                await self.send_bump_reminder()

    async def send_bump_reminder(self):
        """Sends a bump reminder to the specified channel."""
        if self.bump_channel_id:
            channel = self.bot.get_channel(self.bump_channel_id)
            if channel:
                self.bump_waiting = True
                await channel.send("⏰ It's time to use `/bump`!")

async def setup(bot):
    await bot.add_cog(BumpReminder(bot))