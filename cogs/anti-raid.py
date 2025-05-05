import discord
from discord.ext import commands
import asyncio
import time
from datetime import datetime

class NukeProtection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False  # Nuke detection is inactive by default
        self.recent_deletions = []  # Tracks deleted channels
        self.recent_messages = []  # Tracks message spams
        self.raid_threshold = 5  # Number of suspicious actions to consider a raid
        self.raid_detection_time = 10  # Time in seconds to detect a nuke raid
        self.raid_attempts = []  # List of raid attempts with details

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Detects channel deletions."""
        if self.active:
            current_time = time.time()
            self.recent_deletions.append((current_time, channel))

            # Clean up entries older than the detection threshold
            self.recent_deletions = [
                deletion for deletion in self.recent_deletions
                if current_time - deletion[0] <= self.raid_detection_time
            ]

            # If the number of deletions exceeds the threshold, a nuke is detected
            if len(self.recent_deletions) >= self.raid_threshold:
                await self.apply_nuke_sanction()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detects message spamming."""
        if self.active and not message.author.bot:
            current_time = time.time()
            self.recent_messages.append((current_time, message))

            # Clean up messages older than the detection threshold
            self.recent_messages = [
                msg for msg in self.recent_messages
                if current_time - msg[0] <= self.raid_detection_time
            ]

            # If the number of messages exceeds the threshold, it's considered spam
            if len(self.recent_messages) >= self.raid_threshold:
                await self.apply_nuke_sanction()

    async def apply_nuke_sanction(self):
        """Applies a sanction to the nuke author (assigns the Prisoner role)."""
        # Assume the author is the last user to perform an action
        last_action = self.recent_deletions[-1] if len(self.recent_deletions) > 0 else self.recent_messages[-1]
        author = last_action[1].author if isinstance(last_action[1], discord.Message) else last_action[1].guild.owner

        role = discord.utils.get(author.guild.roles, name="Prisoner")
        if role:
            await author.add_roles(role)
            embed = discord.Embed(
                title="Sanction: Prison",
                description=f"{author.mention} has been sent to prison for attempting a nuke raid.",
                color=discord.Color.red()
            )
            await author.send(embed=embed)

        # Log the nuke attempt
        self.raid_attempts.append({
            'author': author,
            'time': datetime.utcnow(),
            'action': 'Nuke - Channel Deletions or Spam'
        })

    @commands.command(name="raid_a", description="Activate nuke raid detection.")
    async def activate_nuke_detection(self, ctx):
        """Activates nuke raid detection."""
        self.active = True
        await ctx.send("Nuke raid detection is now **activated**.", ephemeral=True)

    @commands.command(name="raid_d", description="Deactivate nuke raid detection.")
    async def deactivate_nuke_detection(self, ctx):
        """Deactivates nuke raid detection."""
        self.active = False
        await ctx.send("Nuke raid detection is now **deactivated**.", ephemeral=True)

    @commands.command(name="raid_t", description="View details of nuke raid attempts.")
    async def view_raid_attempts(self, ctx):
        """Displays details of nuke raid attempts."""
        if not self.raid_attempts:
            await ctx.send("No nuke raid attempts recorded.")
            return

        embed = discord.Embed(
            title="Nuke Raid Attempts",
            color=discord.Color.blue()
        )
        for attempt in self.raid_attempts:
            embed.add_field(
                name=f"Raid on {attempt['time'].strftime('%Y-%m-%d %H:%M:%S')}",
                value=f"**Author:** {attempt['author'].mention}\n"
                      f"**Action:** {attempt['action']}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NukeProtection(bot))