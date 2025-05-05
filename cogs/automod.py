import discord
from discord.ext import commands
from datetime import datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod_active = False
        self.banned_words = [
            "pute", "connard", "salope", "batard", "enculé", "niqué", "putain", 
            "con", "connasse", "nigga", "nigger", "raciste", "homo", "gouine", "lesbienne", 
            "pd", "gogole", "sale chien", "sucer", "baiser", "trou du cul", "branlette", 
            "degage", "fils de pute", 
            "merdeux", "tapette", "enculer", "mangeur de merde", "fils de chien", "conasse", 
            "gros con", "sale pute", "grosse merde", "enculé de ta mère", "tarlouze", 
            "foutre", "connard de merde", "ferme ta gueule", "nique ta mère", "nique sa mère", 
            "sucer des bites", "boudin", "bête de sexe", "bite", "niquer", "salopard", 
            "batarde", "crétin", "gland", "débile mental", "enfoiré", "feubé", "gros tas de merde", 
            "bordel de merde", "sale raciste", "sale pédé", "bouse", "puceau", "tapette", 
            "t’es qu’une merde", "un sale bâtard", "sale bâtard", "sale enculé", "t’es une salope", 
            "baltringue", "bitard", "pouffiasse", "bordel", "déchets humains", "fils de pute", 
            "bâtard", "raciste de merde", "bite en bois", "sous homme", "merdeux", "sale merde", 
            "pédé", "t’es qu’une tapette", "te faire enculer", "blédard", "niquer ta mère", 
            "sale blaireau", "fils de sale pute", "cndr", "cnrd", "ecl", "bz", "jebz", "je baise ta", "je baize"
            "f-d-p", "f d p", "enculade", "jebztamere", "tg", "ferme ta guel", "ferme tg", "fermetg", "fils de pul", "fils de p"
            "fil de p", "fils de c","fils de t", "batar", "batard"
        ]
        self.user_infractions = {}  # Stocke les infractions des utilisateurs
        self.log_channel_id = 123456789012345678  # Remplacez par l'ID de votre salon de logs

    def normalize_text(self, text):
        """Normalize le texte pour détecter les variantes."""
        import unicodedata
        return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

    async def log_infractions(self, member, infractions):
        """Envoie un message dans le salon de logs avec les détails des infractions."""
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="🚨 User Infraction Logged",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
            embed.add_field(name="Number of Infractions", value=len(infractions), inline=False)
            embed.add_field(
                name="Messages",
                value="\n".join([f"- **Message ID**: {inf['message_id']} | **Content**: {inf['content']}" for inf in infractions]),
                inline=False
            )
            embed.set_footer(text="AutoMod System")
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Vérifie les messages pour les mots interdits."""
        if not self.automod_active or message.author.bot:
            return

        # Normaliser le contenu du message
        normalized_content = self.normalize_text(message.content)
        for word in self.banned_words:
            if word in normalized_content:
                user_id = message.author.id
                user_data = self.user_infractions.setdefault(user_id, [])

                # Ajouter l'infraction
                user_data.append({
                    "message_id": message.id,
                    "content": message.content,
                    "timestamp": datetime.utcnow()
                })

                # Supprimer le message
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, merci d'utiliser un langage respectueux. Votre message a été supprimé.",
                    delete_after=5
                )

                # Si c'est la 3e infraction, envoyer un log
                if len(user_data) == 3:
                    await self.log_infractions(message.author, user_data)

                break

    @commands.hybrid_command(name="automod_active", aliases=["atm_a"], description="Active l'AutoMod.")
    @commands.has_permissions(administrator=True)
    async def automod_active_command(self, ctx):
        if self.automod_active:
            await ctx.send("L'AutoMod est déjà activé.")
            return

        self.automod_active = True
        await ctx.send("L'AutoMod est maintenant activé.")

    @commands.hybrid_command(name="automod_desactive", aliases=["atm_d"], description="Désactive l'AutoMod.")
    @commands.has_permissions(administrator=True)
    async def automod_desactive_command(self, ctx):
        if not self.automod_active:
            await ctx.send("L'AutoMod est déjà désactivé.")
            return

        self.automod_active = False
        await ctx.send("L'AutoMod est maintenant désactivé.")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))