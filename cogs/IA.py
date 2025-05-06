import discord
from discord.ext import commands
import json
import os
import re

MEMBER_COUNT_FILE = "data/member_count.json"
ALLOWED_CHANNELS_FILE = "data/ia_allowed_channels.json"

WELCOME_CHANNEL_ID = 1287840591714979984
LEAVE_CHANNEL_ID = 1316529224047394838

FOUNDERS = {
    582889968855285772: "Nodino",
    866020774320799754: "Minomak"
}

MODERATORS = {
    593437130441752586: "xav4454",
    463081595998568448: "Echo500",
    1033834366822002769: ".calbusto"
}

HALF_MODS = {
    1033834366822002769: ".calbusto",
    1365974697648459847: "tox.py"
}

ROLES = {
    1328089777660235898: "Staff Team",
    1359555946422210760: "Monios Dev Team"
}

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.member_count = load_json(MEMBER_COUNT_FILE, {"count": 101})["count"]
        self.allowed_channels = load_json(ALLOWED_CHANNELS_FILE, {})

    @commands.command()
    async def add_ia(self, ctx, *types):
        channel_id = str(ctx.channel.id)
        self.allowed_channels[channel_id] = types if types else ["all"]
        save_json(ALLOWED_CHANNELS_FILE, self.allowed_channels)
        await ctx.send(f"✅ IA activée pour ce salon avec types: {', '.join(self.allowed_channels[channel_id])}.")

    @commands.command()
    async def remv_ia(self, ctx):
        channel_id = str(ctx.channel.id)
        if channel_id in self.allowed_channels:
            del self.allowed_channels[channel_id]
            save_json(ALLOWED_CHANNELS_FILE, self.allowed_channels)
            await ctx.send("❌ IA désactivée pour ce salon.")
        else:
            await ctx.send("⚠️ Ce salon n'était pas activé pour l'IA.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_id = str(message.channel.id)
        if channel_id not in self.allowed_channels:
            return

        # Auto-count based on bot messages in welcome/leave channels
        if message.channel.id == WELCOME_CHANNEL_ID and message.author == self.bot.user:
            self.member_count += 1
            save_json(MEMBER_COUNT_FILE, {"count": self.member_count})
        elif message.channel.id == LEAVE_CHANNEL_ID and message.author == self.bot.user:
            self.member_count -= 1
            save_json(MEMBER_COUNT_FILE, {"count": self.member_count})

        # Detect questions
        content = message.content.lower()
        if self.should_respond(channel_id, "member"):
            patterns = [
                r"how many members",
                r"member count",
                r"how many people (are )?here",
                r"combien (y a|ya|il y a) (de|d')?membres",
                r"on est combien",
                r"nombre de membres"
            ]
            if any(re.search(p, content) for p in patterns):
                await message.reply(f"We currently have **{self.member_count} members** on the server")
                return

        if self.should_respond(channel_id, "staff"):
            if "who" in content and ("owner" in content or "creator" in content or "fonda" in content):
                names = ", ".join(FOUNDERS.values())
                await message.reply(f"The server was created by {names}!")
                return

            if "moderator" in content or "mod" in content:
                mods = ", ".join(MODERATORS.values())
                await message.reply(f"Current moderators are: {mods}. (We’re still recruiting!)")
                return

            if "half mod" in content:
                half_mods = ", ".join(HALF_MODS.values())
                await message.reply(f"Our half-mods are: {half_mods}.")
                return

    def should_respond(self, channel_id, category):
        types = self.allowed_channels.get(channel_id, [])
        return "all" in types or category in types

async def setup(bot):
    await bot.add_cog(IA(bot))