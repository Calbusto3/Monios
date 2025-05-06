import discord
from discord.ext import commands
from datetime import datetime, timedelta
import unicodedata
import re

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod_active = False
        self.infractions = {}
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
            "hoe", "cum", "jizz", "dickhead", "shithead", "pawjob", "sybau", "kys", "vro"
        ]

    def normalize(self, text: str) -> str:
        # Remove accents, punctuation, and lowercase
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
        return text

    async def log_infraction(self, member: discord.Member, content: str, count: int):
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = discord.Embed(
                title="🚨 AutoMod Infraction",
                description=f"{member.mention} triggered the filter.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Infraction Count", value=str(count), inline=True)
            embed.add_field(name="Message Content", value=content[:1000] or "Empty", inline=False)
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

        normalized = self.normalize(message.content)
        if any(bad in normalized for bad in self.banned_words):
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            await message.channel.send(
                f"{message.author.mention}, your message has been removed for inappropriate content.",
                delete_after=5
            )

            uid = message.author.id
            self.infractions.setdefault(uid, []).append(datetime.utcnow())

            count = len(self.infractions[uid])
            await self.log_infraction(message.author, message.content, count)

            if count == 3:
                await self.warn_user(message.author)
                await self.timeout_user(message.author)

    @commands.hybrid_command(name="automod_on", description="Enable the AutoMod system.")
    @commands.has_permissions(administrator=True)
    async def automod_on(self, ctx):
        if self.automod_active:
            await ctx.send("already **enabled**.")
        else:
            self.automod_active = True
            await ctx.send("good.")

    @commands.hybrid_command(name="automod_off", description="Disable the AutoMod system.")
    @commands.has_permissions(administrator=True)
    async def automod_off(self, ctx):
        if not self.automod_active:
            await ctx.send("already.")
        else:
            self.automod_active = False
            await ctx.send("done.")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))