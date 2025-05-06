import discord
from discord.ext import commands
import asyncio

class PotitbotAutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activities = [
            discord.Activity(type=discord.ActivityType.playing,name="Minecraft"),
            discord.Activity(type=discord.ActivityType.streaming, name="Monios C.", url="https://www.twitch.tv/monios"),
            discord.Activity(type=discord.ActivityType.listening, name="Calbusto speak"),
        ]

    async def change_activity(self):
        """Change l'activité du bot toutes les 10 secondes."""
        while True:
            for activity in self.activities:
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(60)  # Temps entre chaque activité (en secondes)

    @commands.Cog.listener()
    async def on_ready(self):
        """Quand le bot est prêt, on commence à changer d'activité."""
        print(f"{self.bot.user} est maintenant en ligne!")
        self.bot.loop.create_task(self.change_activity())  # Lancer la fonction en tâche de fond

# L'ajout du cog
async def setup(bot):
    await bot.add_cog(PotitbotAutoMod(bot))