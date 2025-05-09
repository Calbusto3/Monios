import discord
from discord.ext import commands
from datetime import datetime, timedelta
import unicodedata
import re
from typing import Optional

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_settings = {}  # {guild_id: {"active": bool, "infractions": {}, "mutes": {}}}
        self.timeout_duration = timedelta(minutes=10)
        self.log_channel_id = 1369380240333213918

        self.ban_words1 = [

            # French & English insults
            "pute", "connard", "salope", "encule", "niqué", "connasse",
            "trou du cul", "fils de pute", "enculer", "conasse",
            "gros con", "sale pute", "tarlouze", "ferme ta gueule", "ftg", "enfoire",
            "tapette", "cndr", "cnrd", "ecl", "tdc", "ferme tg",
            "fermetg", "batar",
            "fucking", "motherfucker", "bitch", "asshole", "bastard", "cunt",
            "bullshit", "fag", "faggot", "retard", "dumbass", "cock",
            "touch", "dipshit", "bitchass", "fuck off", "twat",
            "hoe", "jizz", "dickhead", "shithead", "sybau", "kys", "vro", "nkvm",
            "childs porn","child porn",
            ] 
        self.ban_words2 = [ 

            # French & English insults
            "baise", "viole", "viol", "nègre", "negro",
            "rape", "r4pe", "r@pe","r4p3", "rap3", " :grape: you"
            "nigger", "nigga", "niga", "ni**a", "n1gga",
            "suck my dick", "suck me", "dick", "d1ck", "d!ck",
            "pussy", "pusy", "pussi", "p@ssy", "p*ssy",
            "wiener", "weenr", "w1ener",
            "kill yourself", "kys", "go die",
            "gas the jews", "hitler", "h1tl3r",
            "retard", "r3tard", "r*tard",
            "faggot", "f@g", "faqqot", "f4ggot",
            "child porn", "cp", "groom", "grooming",
            "rape you", "rape u", "kill you", "kil u", "nazi"
            ]  # Words that trigger immediate mute

        self.ignored_members = {1033834366822002769, 582889968855285772, 866020774320799754}
        self.ignored_roles = {1369727387792707786}
        self.ignored_channels = {1368610600111968387}

        # Ajouter une liste de mots-clés exemptés
        self.exempt_words = [
            "violet", "violette", "violon", "violoncelle", "non-violence", "non-violent", "survol", "voler", "vol", "inviolable",
            "confiance", "conforme", "conformité", "conjugaison", "conscience", "connaissance", "conseil", "contact", "contenu", 
            "contre", "construire", "condition", "conclusion", "connecté", "connexion", "conception", "concentration", "conférence",
            "dispute", "réputation", "permutation", "chute", "substitution", "contribution", "statut", "attribut", "substitut", "constituer",
            "enclume", "enclos", "encodé", "encrier", "enclencher", "enclavé",
            "technique", "pique", "boutonnique", "brique", "dominique", "musique", "pique-nique", "manique", "monastique", "nationale unique", "éthique",
            "traduction", "tédéce", "tendance", "tandis", "traducteur", "dictionnaire", "discours", "culinaire",
            "fermeture", "fermetures", "ferme-auberge", "fermer", "ferment", "fermentation", "ftg-pôle", "futur tg",
            "battard", "bâtardise", "bâtardeau", "battement", "bataillon", "batterie", "bataille", "batave",
            "bull", "bulles", "bull-terrier", "bullish", "sheet", "shift", "shutdown", "shooting",
            "dickens", "dicky", "dickinson", "dickson", "mordicus", "didactique", "syndic", "édicté",
            "cocktail", "cockpit", "cockatoo", "cockburn", "peacock", "rock", "block", "knock",
            "poussycat", "push", "poussée", "poussin", "poussif", "poussière",
            "wienerschnitzel", "vienne", "viennois", "viennoiserie", "viennese",
            "fagot", "fagotin", "fagoter", "fagersta", "flag", "flagrant", "fagotage", "fagan",
            "retarder", "retardataire", "retardé", "retardement", "retardement tactique", "retardateur",
            "grape", "grapefruit", "rapé", "rapide", "rappel", "rapace", "rap", "rapper", "rappelé", "rapatriement",
            "kyste", "kylian", "kyle", "kayak", "krypton", "kyrie", "kiss", "kits", "kyushu", "kysler", "kynurenine",
            "fucoidan", "fulgurant", "fucoxanthin", "funk", "funky", "fukuoka", "function", "flux",
            "association", "assurance", "assis", "assistant", "assiette", "assemblée", "assigné", "assidu",
            "bitchy", "bitche", "bitume", "bithynien",
            "tapet", "tapis", "taper", "taperie", "tapotement", "tapoté",
            "shoe", "whole", "holes", "home", "homéopathe", "homologue", "hoenn", "hold", "hobby",
            "jazz", "fizz", "blizzard", "jezz", "jizzle", "puzzle",
            "sybille", "sybarite", "sybase", "sybaris", "syllabus",
            "vroum", "vroom", "vront", "vroon",
            "cendre", "cendrier", "cendrillon", "cendreux",
            "éclat", "éclair", "éclaire", "éclatement", "éclaireur", "éclater",
            "nazi-antifa", "nazisme historique", "nazca", "nazareen"

        ]

    # Modifier la méthode de normalisation pour exclure les mots exemptés
    def normalize(self, text: str) -> str:
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        normalized_text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
        # Supprimer les mots exemptés
        for exempt_word in self.exempt_words:
            normalized_text = normalized_text.replace(exempt_word, "")
        return normalized_text

    def get_guild_data(self, guild_id):
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                "active": False,
                "infractions": {},
                "mutes": {}
            }
        return self.guild_settings[guild_id]

    async def log_infraction(self, member, content, count, sanction, banned_words, degree):
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = discord.Embed(
                title="🚨 AutoMod Infraction",
                description=f"{member.mention} broke the language rules.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Banned word(s)", value=", ".join(banned_words), inline=False)
            embed.add_field(name="Severity", value=f"Level {degree}", inline=True)
            embed.add_field(name="Sanction", value=sanction, inline=True)
            embed.add_field(name="Message", value=content[:1000] or "Empty", inline=False)
            if degree == 1:
                embed.add_field(name="Warnings (within 10 mins)", value=f"{count}/5", inline=True)
            embed.add_field(name="Total mutes", value=str(self.guild_settings[member.guild.id]["mutes"].get(member.id, 0)), inline=True)
            await channel.send(embed=embed)

    async def timeout_user(self, member):
        try:
            until = discord.utils.utcnow() + self.timeout_duration
            await member.timeout(until, reason="AutoMod - Automatic sanction")
        except discord.Forbidden:
            pass

    async def warn_user(self, member):
        try:
            await member.send(f"⚠️ You used forbidden language. You are muted for {int(self.timeout_duration.total_seconds() // 60)} minutes.")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_data = self.get_guild_data(message.guild.id)
        if not guild_data["active"]:
            return

        if message.author.id in self.ignored_members:
            return
        if any(role.id in self.ignored_roles for role in message.author.roles):
            return
        if message.channel.id in self.ignored_channels:
            return
        if message.attachments or any(ext in message.content.lower() for ext in [".gif", ".mp4", ".webm"]):
            return

        normalized = self.normalize(message.content)

        found_words_2 = [w for w in self.ban_words2 if w in normalized]
        found_words_1 = [w for w in self.ban_words1 if w in normalized and w not in found_words_2]

        uid = message.author.id
        now = datetime.utcnow()

        # Gestion des mots de degré 2 (mute direct et suppression)
        if found_words_2:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            # Mute immédiat
            await self.warn_user(message.author)
            await self.timeout_user(message.author)
            mutes = guild_data["mutes"]
            mutes[uid] = mutes.get(uid, 0) + 1
            await self.log_infraction(
                message.author, message.content, 1, "Immediate mute", found_words_2, degree=2
            )
            return

        # Gestion des mots de degré 1 (avertissements, pas de suppression)
        if found_words_1:
            infractions = guild_data["infractions"]
            if uid not in infractions:
                infractions[uid] = []
            infractions[uid].append(now)

            # Conserver uniquement les infractions des 10 dernières minutes
            infractions[uid] = [ts for ts in infractions[uid] if now - ts <= timedelta(minutes=10)]
            count = len(infractions[uid])

            await message.channel.send(
                f"{message.author.mention}, forbidden language detected. Warning! {count}/5",
                delete_after=5
            )

            sanction = "Warning"
            if count >= 5:
                sanction = "Mute"
                guild_data["mutes"][uid] = guild_data["mutes"].get(uid, 0) + 1
                await self.warn_user(message.author)
                await self.timeout_user(message.author)

            await self.log_infraction(
                message.author, message.content, count, sanction, found_words_1, degree=1
            )

    @commands.hybrid_command(name="automod_on")
    @commands.has_permissions(administrator=True)
    async def automod_on(self, ctx):
        self.get_guild_data(ctx.guild.id)["active"] = True
        await ctx.send("✅ AutoMod is now **enabled** on this server.")

    @commands.hybrid_command(name="automod_off")
    @commands.has_permissions(administrator=True)
    async def automod_off(self, ctx):
        self.get_guild_data(ctx.guild.id)["active"] = False
        await ctx.send("❌ AutoMod is now **disabled** on this server.")

    @commands.hybrid_command(name="automod_list")
    @commands.has_permissions(administrator=True)
    async def automod_list(self, ctx, member: Optional[discord.Member]):
        if not member:
            await ctx.send("❌ Please mention a member.")
            return

        guild_data = self.get_guild_data(ctx.guild.id)
        infractions = guild_data["infractions"].get(member.id, [])
        mutes = guild_data["mutes"].get(member.id, 0)

        embed = discord.Embed(
            title=f"📋 AutoMod History for {member}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Infractions (last 10 mins)", value=len(infractions), inline=True)
        embed.add_field(name="Mutes (level 1 or 2)", value=mutes, inline=True)

        await ctx.send(embed=embed)

    # Ajouter une commande pour afficher la liste des mots exemptés
    @commands.hybrid_command(name="automod_exempt_list")
    @commands.has_permissions(administrator=True)
    async def automod_exempt_list(self, ctx):
        exempt_words = ", ".join(self.exempt_words) or "No exempt words."
        await ctx.send(f"📋 **Exempt Words:** {exempt_words}")

    # Ajouter une commande pour ajouter un mot à la liste des mots exemptés
    @commands.hybrid_command(name="automod_exempt_add")
    @commands.has_permissions(administrator=True)
    async def automod_exempt_add(self, ctx, *, word: str):
        if word.lower() in self.exempt_words:
            await ctx.send(f"❌ The word `{word}` is already in the exempt list.")
            return
        self.exempt_words.append(word.lower())
        await ctx.send(f"✅ The word `{word}` has been added to the exempt list.")

    # Ajouter une commande pour supprimer un mot de la liste des mots exemptés
    @commands.hybrid_command(name="automod_exempt_remove")
    @commands.has_permissions(administrator=True)
    async def automod_exempt_remove(self, ctx, *, word: str):
        if word.lower() not in self.exempt_words:
            await ctx.send(f"❌ The word `{word}` is not in the exempt list.")
            return
        self.exempt_words.remove(word.lower())
        await ctx.send(f"✅ The word `{word}` has been removed from the exempt list.")

    # Ajouter une vérification pour permettre à l'utilisateur avec l'ID 1033834366822002769 d'utiliser les commandes
    async def cog_check(self, ctx):
        return ctx.author.id == 1033834366822002769 or ctx.author.guild_permissions.administrator

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
