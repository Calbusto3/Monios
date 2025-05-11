import discord
from discord.ext import commands
import random
import string
from datetime import datetime, timedelta

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification_data = {}  # {user_id: {"code": str, "expires_at": datetime, "attempts": int}}
        self.verification_channel_id = None  # Sera défini via la commande
        self.log_channel_id = 1369380240333213918  # Salon des logs
        self.success_roles_add = [1288211650561703936]
        self.success_roles_remove = [1371121192647524363]
        self.failure_roles_add = [1371122322597216397]
        self.failure_roles_remove = [1371121192647524363]
        self.bot_role_id = 1287785206014541967  # Rôle attribué automatiquement aux bots

    @commands.hybrid_command(name="verif_set")
    @commands.has_permissions(administrator=True)
    async def verif_set(self, ctx):
        """Définit le salon et envoie l'embed de vérification."""
        self.verification_channel_id = ctx.channel.id
        embed = discord.Embed(
            title="🔒 Vérification",
            description="Bienvenue sur le serveur ! Cliquez sur le bouton ci-dessous pour commencer la vérification.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Monios sécurité.")
        view = VerificationButton(self)
        await ctx.send(embed=embed, view=view)

    async def handle_verification(self, interaction: discord.Interaction):
        """Génère et envoie le code de vérification."""
        member = interaction.user
        if member.bot:
            bot_role = member.guild.get_role(self.bot_role_id)
            if bot_role:
                await member.add_roles(bot_role)
            await interaction.response.send_message("🤖 Bot détecté. Vérification automatique réussie.", ephemeral=True)
            return

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        self.verification_data[member.id] = {"code": code, "expires_at": expires_at, "attempts": 0}

        try:
            await member.send(f"🔐 Votre code de vérification est : `{code}`.\nVous avez 5 minutes pour l'entrer dans le salon de vérification.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Impossible de vous envoyer un message privé. Activez vos MP.", ephemeral=True)
            return

        await interaction.response.send_message("📩 Un code vous a été envoyé en message privé. Entrez-le ici dans les 5 minutes.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.verification_channel_id or message.channel.id != self.verification_channel_id:
            return
        if message.author.bot:
            return

        member = message.author
        data = self.verification_data.get(member.id)
        if not data:
            await message.delete()
            return

        # Code expiré
        if datetime.utcnow() > data["expires_at"]:
            del self.verification_data[member.id]
            await message.delete()
            await message.channel.send(f"{member.mention}, votre code a expiré. Veuillez recommencer la vérification.", delete_after=5)
            return

        # Code correct
        if message.content.strip() == data["code"]:
            await self._apply_roles(member, success=True, attempts=data["attempts"])
            del self.verification_data[member.id]
            await message.delete()
            return

        # Tentative échouée
        data["attempts"] += 1
        if data["attempts"] >= 5:
            del self.verification_data[member.id]
            await self._apply_roles(member, success=False, attempts=5)
            await message.delete()
            return

        await message.delete()
        await message.channel.send(f"{member.mention}, code incorrect. Il vous reste {5 - data['attempts']} tentative(s).", delete_after=5)

    async def _apply_roles(self, member, success: bool, attempts: int):
        """Applique les rôles selon réussite ou échec et envoie un log."""
        if success:
            for role_id in self.success_roles_add:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            for role_id in self.success_roles_remove:
                role = member.guild.get_role(role_id)
                if role:
                    await member.remove_roles(role)
            log_embed = discord.Embed(
                title="✅ Vérification réussie",
                description=f"{member.mention} a réussi la vérification.",
                color=discord.Color.green()
            )
        else:
            for role_id in self.failure_roles_add:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            for role_id in self.failure_roles_remove:
                role = member.guild.get_role(role_id)
                if role:
                    await member.remove_roles(role)
            log_embed = discord.Embed(
                title="❌ Vérification échouée",
                description=f"{member.mention} a échoué à se vérifier.",
                color=discord.Color.red()
            )

        log_embed.add_field(name="Tentatives", value=str(attempts), inline=False)
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=log_embed)

class VerificationButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Se vérifier", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_verification(interaction)

async def setup(bot):
    await bot.add_cog(Verification(bot))