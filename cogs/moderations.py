import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    # mute
    @commands.hybrid_command(name="mute", description="Mute un membre pendant une durée spécifiée.")
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int, reason: str = None):
        """Mute un membre pour une durée spécifiée."""
        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return

        # Calcul de la durée de mute en secondes
        mute_duration = timedelta(minutes=duration)
        
        try:
            # Application du mute
            await member.timeout(mute_duration, reason=reason)
            await ctx.send(f"{member} a été mute pour {duration} minutes. Raison: {reason if reason else 'Aucune'}.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite : {str(e)}")

    # unmute
    @commands.hybrid_command(name="unmute", description="Unmute un membre.")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Unmute un membre pour lui permettre de parler à nouveau."""
        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return

        try:
            # Annulation du mute
            await member.timeout(None)
            await ctx.send(f"{member} a été unmute.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite : {str(e)}")
                  
    # ban
    @commands.hybrid_command(name="ban", description="Bannir un membre du serveur.")
    async def ban(self, ctx: commands.Context, member: discord.Member = None, reason: str = None):
        # Vérification des permissions
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("❌ Vous n'avez pas la permission de bannir les membres.")
            return

        # Si aucun membre n'est mentionné, renvoyer un message d'erreur
        if member is None:
            await ctx.send("❌ Veuillez mentionner un membre à bannir.")
            return

        # Tentative de bannir le membre
        try:
            # Bannir le membre avec une raison
            await member.ban(reason=reason)
            
            # Création du message Embed
            embed = discord.Embed(
                title="Vous avez été banni du serveur",
                description=f"Vous avez été banni du serveur pour la raison suivante : {reason if reason else 'Aucune raison spécifiée.'}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Pour contester ce ban, veuillez passer par ce formulaire.")
            embed.add_field(name="Formulaire de contestation", value="[Cliquez ici pour contester le ban](https://forms.gle/RKeGRaaBsrYHQXAp6)", inline=False)

            # Envoi de l'embed en DM au membre banni
            await member.send(embed=embed)

            # Message de confirmation dans le serveur
            await ctx.send(f"{member} a été banni avec succès pour la raison : {reason if reason else 'Aucune.'}")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de bannir ce membre.")
        except discord.HTTPException:
            await ctx.send("❌ Une erreur s'est produite en tentant de bannir ce membre.")

    # unban
    @commands.hybrid_command(name="unban", description="Unbannir un membre du serveur.")
    async def unban(self, ctx: commands.Context, user_id: int, reason: str = None):
        # Vérification des permissions
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("❌ Vous n'avez pas la permission de unban les membres.")
            return

        # Tentative de unban
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"{user} a été débanni avec succès.")
        except discord.NotFound:
            await ctx.send("❌ Aucun membre correspondant à cet ID n'a été trouvé.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour effectuer cette action.")

    @commands.hybrid_command(name="delete", aliases=["del"], with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def delete(self, ctx: commands.Context, count: int):
        await ctx.message.delete()  # Immediately delete the command message.

        if count < 1:
            await ctx.send("You must specify a valid number greater than 0.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=count)
        
        # Confirmation message.
        confirmation = await ctx.send(f"🗑️ {len(deleted)} message(s) deleted.")
        await confirmation.delete(delay=5)
        
    @commands.hybrid_command(name="reset", help="Reset a channel.")
    @commands.has_permissions(manage_messages=True)
    async def reset(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.purge()
        reset_message = await channel.send("Channel successfully reset.")
        await reset_message.delete(delay=5)
            
async def setup(bot):
    await bot.add_cog(Moderation(bot))
