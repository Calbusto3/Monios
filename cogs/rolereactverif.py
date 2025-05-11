import discord
from discord.ext import commands

class RoleReactVerif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flag_roles = {
            "🇺🇸": 123456789012345678,  # English
            "🇫🇷": 123456789012345679,  # French
            "🇸🇦": 123456789012345680,  # Arabic
            "🇪🇸": 123456789012345681,  # Spanish
            "🇮🇹": 123456789012345682,  # Italian
            "🇩🇪": 123456789012345683,  # German
            "🇳🇱": 123456789012345684,  # Dutch
            "🇵🇹": 123456789012345685,  # Portuguese
            "🇸🇪": 123456789012345686,  # Swedish
            "🇹🇷": 123456789012345687,  # Turkish
            "🇨🇳": 123456789012345688,  # Chinese
            "🇷🇺": 123456789012345689   # Russian
        }

    @commands.command(name="rolereactverif")
    @commands.has_permissions(administrator=True)
    async def rolereactverif(self, ctx):
        embed = discord.Embed(
            title="🌍 Language Selection / Sélection de la langue",
            description=(
                "**🇺🇸 English**: React with 🇺🇸 to select English.\n"
                "**🇫🇷 Français**: Réagis avec 🇫🇷 pour choisir le français.\n"
                "**🇸🇦 العربية**: اضغط على 🇸🇦 لاختيار العربية.\n"
                "**🇪🇸 Español**: Reacciona con 🇪🇸 para seleccionar español.\n"
                "**🇮🇹 Italiano**: Reagisci con 🇮🇹 per selezionare l'italiano.\n"
                "**🇩🇪 Deutsch**: Reagiere mit 🇩🇪, um Deutsch zu wählen.\n"
                "**🇳🇱 Nederlands**: Reageer met 🇳🇱 om Nederlands te kiezen.\n"
                "**🇵🇹 Português**: Reaja com 🇵🇹 para selecionar português.\n"
                "**🇸🇪 Svenska**: Reagera med 🇸🇪 för att välja svenska.\n"
                "**🇹🇷 Türkçe**: 🇹🇷 ile tepki vererek Türkçe'yi seçin.\n"
                "**🇨🇳 中文**: 反应 🇨🇳 以选择中文。\n"
                "**🇷🇺 Русский**: Нажмите 🇷🇺, чтобы выбрать русский."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Select your language(s) by reacting below.")

        message = await ctx.send(embed=embed)
        for emoji in self.flag_roles:
            await message.add_reaction(emoji)

        # Enregistre l’ID du message si tu veux le retrouver plus tard
        self.language_message_id = message.id
        self.language_channel_id = ctx.channel.id

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id != getattr(self, "language_message_id", None):
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_id = self.flag_roles.get(str(payload.emoji.name))
        if role_id:
            role = guild.get_role(role_id)
            if role:
                await member.add_roles(role, reason="Langue sélectionnée via réaction")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id != getattr(self, "language_message_id", None):
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_id = self.flag_roles.get(str(payload.emoji.name))
        if role_id:
            role = guild.get_role(role_id)
            if role:
                await member.remove_roles(role, reason="Langue retirée via réaction")


async def setup(bot):
    await bot.add_cog(RoleReactVerif(bot))