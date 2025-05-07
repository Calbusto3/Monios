import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from keep_alive import keep_alive
from threading import Thread
from flask import Flask
import asyncio

# Charger les variables d'environnement
load_dotenv()
token = os.getenv('TOKEN')

# Vérification du token
if not token:
    print("❌ Le token du bot est manquant. Assurez-vous que le fichier .env contient 'DISCORD_TOKEN=your_token_here'.")
    exit(1)

# Configurer Flask pour garder le bot en vie
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is alive!', 200

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Lancer Flask dans un thread séparé
thread = Thread(target=run_flask)
thread.start()

# Classe du bot
class MonBot(commands.Bot):
    async def setup_hook(self):
        # Charger les cogs dynamiquement mais éviter de les recharger si déjà chargés
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                extension = filename[:-3]
                if extension not in self.cogs:
                    try:
                        await self.load_extension(f'cogs.{extension}')
                        print(f"✅ {extension} cog chargé avec succès.")
                    except Exception as e:
                        print(f"❌ Erreur lors du chargement de {extension} : {type(e).__name__} - {e}")
                else:
                    print(f"⚠️ {extension} cog déjà chargé, saut de son chargement.")
        
        # Attendre un petit moment avant de synchroniser
        await asyncio.sleep(1)

        # Synchroniser les commandes
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} commande(s) slash/hybride(s) synchronisée(s).")
        except Exception as e:
            print(f"❌ Erreur lors de la synchronisation des commandes : {type(e).__name__} - {e}")

# Configurer les intents
intents = discord.Intents.all()

bot = MonBot(command_prefix=".", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"🤖 Bot prêt ! Connecté en tant que {bot.user} (ID : {bot.user.id})")

try:
    keep_alive()
except Exception as e:
    print(f"❌ Erreur dans keep_alive : {type(e).__name__} - {e}")

# Démarrer le bot avec le token
try:
    bot.run(token)
except Exception as e:
    print(f"❌ Erreur lors du démarrage du bot : {type(e).__name__} - {e}")