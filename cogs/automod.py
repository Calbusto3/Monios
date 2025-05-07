import discord
from discord.ext import commands
from datetime import datetime, timedelta
import unicodedata
import re
from typing import Optional

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod_active = False
        self.infractions = {}  # {user_id: [timestamps]}
        self.mute_count = {}  # {user_id: count of 5/5 infractions}
        self.log_channel_id = 1369380240333213918
        self.timeout_duration = timedelta(minutes=10)

        self.banned_words = [
            # French & English insults
            "pute", "connard", "salope", "batard", "encule", "niqué", "connasse", "pd",
            "sucer", "trou du cul", "branlette", "fils de pute", "enculer", "conasse",
            "gros con", "sale pute", "tarlouze", "ferme ta gueule", "bite", "enfoire",
            "pede", "tapette", "salope", "pouffiasse", "cndr", "cnrd", "ecl", "bz",
            "baise t", "baize", "fdp", "jebztamere", "ftg", "ferme tg",
            "fermetg", "fils de c", "fils de t", "batar",
            "fucking", "motherfucker", "bitch", "dick", "asshole", "bastard", "cunt",
            "slut", "whore", "bullshit", "fag", "faggot", "retard", "dumbass", "cock",
            "pussy", "douche", "nigga", "nigger", "jerk off", "blowjob", "dipshit",
            "suck my dick", "suck my cock", "bitchass", "fuck off", "get fucked", "twat",
            "hoe", "cum", "jizz", "dickhead", "shithead", "pawjob", "sybau", "kys", "vro", "tgrm",
            "ftcht", "tgrmlpt", "suicide", "tg", "guel", "gel"
        ]

        # Lists for ignored members, roles, and channels
        self.ignored_members = {1033834366822002769}  # Add member IDs here
        self.ignored_roles = {1369727387792707786}    # Add role IDs here
        self.ignored_channels = {1368610600111968387} # Add channel IDs here

    def normalize(self, text: str) -> str:
        # Remove accents, punctuation, and lowercase
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
        return text

    async def log_infraction(self, member: discord.Member, content: str, count: int, sanction: str, banned_words_used: list):
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = discord.Embed(
                title="🚨 AutoMod Infraction",
                description=f"{member.mention} triggered the filter.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Infraction Count", value=f"{count}/5", inline=True)
            embed.add_field(name="Sanction", value=sanction, inline=True)
            embed.add_field(name="Banned Words Used", value=", ".join(banned_words_used), inline=False)
            embed.add_field(name="Message Content", value=content[:1000] or "Empty", inline=False)
            embed.add_field(name="5/5 Count", value=str(self.mute_count.get(member.id, 0)), inline=True)
            await channel.send(embed=embed)

    async def timeout_user(self, member: discord.Member):
        until = discord.utils.utcnow() + self.timeout_duration
        try:
            await member.timeout(until, reason="AutoMod - Too many infractions")
        except discord.Forbidden:
            pass

    async def warn_user(self, member: discord.Member):
        try:
            await member.send(
                f"⚠️ You have used prohibited language multiple times and have been automatically muted for {int(self.timeout_duration.total_seconds() // 60)} minutes."
            )
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.automod_active or message.author.bot or not message.guild:
            return

        # Ignorer les messages contenant uniquement des GIFs ou des fichiers multimédias
        if message.attachments or any(ext in message.content.lower() for ext in [".gif", ".mp4", ".webm"]):
            return

        # Check if the member, role, or channel is ignored
        if message.author.id in self.ignored_members:
            return
        if any(role.id in self.ignored_roles for role in message.author.roles):
            return
        if message.channel.id in self.ignored_channels:
            return

        normalized = self.normalize(message.content)
        banned_words_used = [bad for bad in self.banned_words if bad in normalized]
        if banned_words_used:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            uid = message.author.id
            now = datetime.utcnow()

            # Initialize infraction tracking for the user
            if uid not in self.infractions:
                self.infractions[uid] = []
            self.infractions[uid].append(now)

            # Remove infractions older than 10 minutes
            self.infractions[uid] = [ts for ts in self.infractions[uid] if now - ts <= timedelta(minutes=10)]

            count = len(self.infractions[uid])

            # Send warning message
            await message.channel.send(
                f"{message.author.mention}, you have used a banned word on the server. Please watch your language. {count}/5",
                delete_after=5
            )

            # Log the infraction
            sanction = "Warning"
            if count == 5:
                sanction = "Mute"
                # Increment mute count
                self.mute_count[uid] = self.mute_count.get(uid, 0) + 1
                await self.warn_user(message.author)
                await self.timeout_user(message.author)

            await self.log_infraction(message.author, message.content, count, sanction, banned_words_used)

    @commands.hybrid_command(name="automod_on", description="Enable the AutoMod system.")
    @commands.has_permissions(administrator=True)
    async def automod_on(self, ctx):
        if self.automod_active:
            await ctx.send("AutoMod is already **enabled**.")
        else:
            self.automod_active = True
            await ctx.send("AutoMod has been **enabled**.")

    @commands.hybrid_command(name="automod_off", description="Disable the AutoMod system.")
    @commands.has_permissions(administrator=True)
    async def automod_off(self, ctx):
        if not self.automod_active:
            await ctx.send("AutoMod is already **disabled**.")
        else:
            self.automod_active = False
            await ctx.send("AutoMod has been **disabled**.")

    @commands.hybrid_command(name="automod_list", description="Display a member's infractions.")
    @commands.has_permissions(administrator=True)
    async def automod_list(self, ctx, member: Optional[discord.Member]):
        if not member:
            await ctx.send("❌ Please mention a valid member.")
            return

        uid = member.id

        # Check if the member has any recorded infractions
        if uid not in self.infractions and uid not in self.mute_count:
            await ctx.send(f"✅ {member.mention} has no recorded infractions.")
            return

        # Retrieve information
        infractions = self.infractions.get(uid, [])
        mute_count = self.mute_count.get(uid, 0)

        # Build the list of banned words used
        banned_words_used = []
        for timestamp in infractions:
            # Here, we assume that banned words are already logged in `self.infractions` (you can adapt if necessary)
            # If you want to store the exact banned words, you will need to add them to `self.infractions`.
            pass  # Placeholder if you want to add this logic

        # Build the embed
        embed = discord.Embed(
            title=f"📋 Infraction History for {member}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Total Number of Infractions", value=len(infractions), inline=True)
        embed.add_field(name="Number of Mutes (5/5)", value=mute_count, inline=True)
        embed.add_field(name="Banned Words Used", value=", ".join(banned_words_used) if banned_words_used else "None", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))