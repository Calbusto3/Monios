import discord
from discord.ext import commands
import json
import os
import re
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

FAQ_FILE = "data/faqs.json"
CHANNEL_FILE = "data/ia_channel.json"
MEMBER_COUNT_FILE = "data/member_count.json"

WELCOME_CHANNEL = 1287840591714979984
LEAVE_CHANNEL = 1316529224047394838

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        return default
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = load_json(CHANNEL_FILE, [])
        self.faqs = load_json(FAQ_FILE, [])
        self.member_count = load_json(MEMBER_COUNT_FILE, {"count": 100})["count"]

    @commands.command()
    async def add_ia(self, ctx):
        cid = str(ctx.channel.id)
        if cid in self.allowed_channels:
            await ctx.send("⚠️ This channel already has IA enabled.")
            return
        self.allowed_channels.append(cid)
        save_json(CHANNEL_FILE, self.allowed_channels)
        await ctx.send("✅ AI has been enabled in this channel.")

    @commands.command()
    async def remv_ia(self, ctx):
        cid = str(ctx.channel.id)
        if cid not in self.allowed_channels:
            await ctx.send("⚠️ This channel does not have IA enabled.")
            return
        self.allowed_channels.remove(cid)
        save_json(CHANNEL_FILE, self.allowed_channels)
        await ctx.send("❌ AI has been disabled in this channel.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        cid = str(message.channel.id)
        content = message.content.lower()

        # Gestion auto du nombre de membres
        if message.channel.id == WELCOME_CHANNEL and message.author == self.bot.user:
            self.member_count += 1
            save_json(MEMBER_COUNT_FILE, {"count": self.member_count})
        elif message.channel.id == LEAVE_CHANNEL and message.author == self.bot.user:
            self.member_count -= 1
            save_json(MEMBER_COUNT_FILE, {"count": self.member_count})

        if cid not in self.allowed_channels:
            return

        # 1. FAQ Check
        for faq in self.faqs:
            if re.search(faq["question"], content):
                response = faq["response"].replace("{member_count}", str(self.member_count))
                await message.reply(response)
                return

        # 2. Ping or fallback to OpenAI
        if self.bot.user in message.mentions:
            await message.channel.typing()
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Monios' helpful Discord assistant."},
                        {"role": "user", "content": message.content}
                    ]
                )
                answer = response['choices'][0]['message']['content']
                await message.reply(answer)
            except openai.error.RateLimitError as e:
                await message.reply(f"❌ Limite d'utilisation atteinte pour l'API OpenAI : {e}")
            except Exception as e:
                await message.reply(f"❌ Erreur avec l'API OpenAI :\n```{e}```")


async def setup(bot):
    await bot.add_cog(IA(bot))