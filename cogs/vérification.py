import discord
from discord.ext import commands
import random
import string
from datetime import datetime, timedelta

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification_data = {}  # {member_id: {"code": str, "expires_at": datetime, "attempts": int}}
        self.verification_channel_id = None
        self.log_channel_id = None
        self.success_roles_add = [1288211650561703936]  # Rôles à ajouter en cas de succès
        self.success_roles_remove = [1371121192647524363]  # Rôles à retirer en cas de succès
        self.failure_roles_add = [1371122322597216397]  # Rôles à ajouter en cas d'échec
        self.failure_roles_remove = [1371121192647524363]  # Rôles à retirer en cas d'échec
        self.bot_role_id = 1287785206014541967  # Rôle pour les bots

    @commands.hybrid_command(name="verif_set")
    @commands.has_permissions(administrator=True)
    async def verif_set(self, ctx):
        """Envoie l'embed de vérification avec un bouton."""
        self.verification_channel_id = ctx.channel.id
        embed = discord.Embed(
            title="🔒 Vérification",
            description="Bienvenue sur le serveur ! Cliquez sur le bouton ci-dessous pour commencer la vérification.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Monios sécurité.")
        view = VerificationButton(self)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="verifier")
    @commands.has_permissions(administrator=True)
    async def verifier(self, ctx, member: discord.Member):
        """Vérifie manuellement un membre."""
        await self.grant_roles(member, success=True)
        await ctx.send(f"✅ {member.mention} a été vérifié manuellement.")

    async def grant_roles(self, member, success: bool):
        """Ajoute ou retire les rôles en fonction du succès ou de l'échec."""
        if success:
            # Gestion des rôles en cas de succès
            for role_id in self.success_roles_add:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            for role_id in self.success_roles_remove:
                role = member.guild.get_role(role_id)
                if role:
                    await member.remove_roles(role)
        else:
            # Gestion des rôles en cas d'échec
            for role_id in self.failure_roles_add:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            for role_id in self.failure_roles_remove:
                role = member.guild.get_role(role_id)
                if role:
                    await member.remove_roles(role)

    async def handle_verification(self, interaction: discord.Interaction):
        """Gère la vérification lorsqu'un membre clique sur le bouton."""
        member = interaction.user
        if member.bot:
            # Si c'est un bot, on lui donne directement le rôle défini
            bot_role = member.guild.get_role(self.bot_role_id)
            if bot_role:
                await member.add_roles(bot_role)
            await interaction.response.send_message("🤖 Bot détecté. Vérification automatique réussie.", ephemeral=True)
            return

        # Générer un code unique
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        self.verification_data[member.id] = {"code": code, "expires_at": expires_at, "attempts": 0}

        # Envoyer le code en MP
        try:
            await member.send(f"🔑 Votre code de vérification est : `{code}`. Vous avez 5 minutes pour le saisir dans le salon de vérification.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Impossible de vous envoyer un message privé. Activez vos MP.", ephemeral=True)
            return

        # Répondre dans le salon de vérification
        await interaction.response.send_message("📩 Un code unique vous a été envoyé en MP. Veuillez le saisir ici.", ephemeral=True)

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

        # Vérifier si le code est expiré
        if datetime.utcnow() > data["expires_at"]:
            del self.verification_data[member.id]
            await message.delete()
            await message.channel.send(f"{member.mention}, votre code a expiré. Veuillez recommencer la vérification.", delete_after=5)
            return

        # Vérifier le code
        if message.content.strip() == data["code"]:
            await self.grant_roles(member, success=True)
            del self.verification_data[member.id]
            await message.delete()
            await message.channel.send(f"✅ {member.mention}, vous avez été vérifié avec succès.", delete_after=5)

            # Log de succès
            if self.log_channel_id:
                log_channel = self.bot.get_channel(self.log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="✅ Vérification réussie",
                        description=f"{member.mention} a été vérifié avec succès.",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Tentatives", value=data["attempts"], inline=False)
                    await log_channel.send(embed=embed)
            return

        # Gestion des échecs
        data["attempts"] += 1
        if data["attempts"] >= 5:
            del self.verification_data[member.id]
            await self.grant_roles(member, success=False)
            await message.delete()
            await message.channel.send(f"❌ {member.mention}, vous avez échoué trop de fois.", delete_after=5)

            # Log d'échec
            if self.log_channel_id:
                log_channel = self.bot.get_channel(self.log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="❌ Vérification échouée",
                        description=f"{member.mention} a échoué la vérification.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Tentatives", value=data["attempts"], inline=False)
                    await log_channel.send(embed=embed)
            return

        # Si le code est incorrect mais qu'il reste des tentatives
        await message.delete()
        await message.channel.send(f"{member.mention}, le code est incorrect. Veuillez réessayer.", delete_after=5)

class VerificationButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Se vérifier", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_verification(interaction)

async def setup(bot):
    await bot.add_cog(Verification(bot))