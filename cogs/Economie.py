import json
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import asyncio


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.shop = []
        self.inventories = {}
        self.levels = {}
        self.currency = "💰"
        self.load_data()

    # Save data to a JSON file
    def save_data(self):
        with open("economy.json", "w") as file:
            json.dump({
                "balances": self.data,
                "shop": self.shop,
                "inventories": self.inventories,
                "levels": self.levels,
                "currency": self.currency,
            }, file)

    # Load data from a JSON file
    def load_data(self):
        try:
            with open("economy.json", "r") as file:
                data = json.load(file)
                self.data = data.get("balances", {})
                self.shop = data.get("shop", [])
                self.inventories = data.get("inventories", {})
                self.levels = data.get("levels", {})
                self.currency = data.get("currency", "💰")
        except FileNotFoundError:
            self.data = {}
            self.shop = []
            self.inventories = {}
            self.levels = {}
            self.currency = "💰"

    # Calculate XP required for the next level
    def xp_required(self, level):
        return 50 + (level - 1) * 25

    # Add XP and handle leveling up
    def add_xp(self, user_id, xp):
        user_data = self.levels.get(user_id, {"level": 1, "xp": 0})
        user_data["xp"] += xp

        while user_data["xp"] >= self.xp_required(user_data["level"]):
            user_data["xp"] -= self.xp_required(user_data["level"])
            user_data["level"] += 1
            reward = 10 + (user_data["level"] - 1) * 5
            self.data[user_id] = self.data.get(user_id, 0) + reward

        self.levels[user_id] = user_data
        self.save_data()

    # Create a progress bar for XP
    def create_progress_bar(self, progress, total, bar_length=20):
        percentage = (progress / total) * 100
        filled_length = int(bar_length * progress // total)
        empty_length = bar_length - filled_length
        return f"{'█' * filled_length}{'░' * empty_length} {round(percentage, 2)}%"

    # Command to view a member's level
    @app_commands.command(name="level", description="View your level or another member's level.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        user_id = str(member.id)
        user_data = self.levels.get(user_id, {"level": 1, "xp": 0})
        xp_required = self.xp_required(user_data["level"])
        progress_bar = self.create_progress_bar(user_data["xp"], xp_required)

        embed = discord.Embed(
            title=f"🎖 Level of {member.display_name}",
            description=(
                f"**Level**: {user_data['level']}\n"
                f"**XP**: {user_data['xp']} / {xp_required}\n"
                f"**Progress**: {progress_bar}"
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    # Command to view the leaderboard with pagination
    class LevelLeaderboard(View):
        def __init__(self, leaderboard, current_page=0):
            super().__init__()
            self.leaderboard = leaderboard
            self.current_page = current_page

        def get_page(self):
            start = self.current_page * 7
            end = start + 7
            return self.leaderboard[start:end]

        @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.primary)
        async def prev_page(self, interaction: discord.Interaction, button: Button):
            if self.current_page > 0:
                self.current_page -= 1
                await self.update_page(interaction)

        @discord.ui.button(label="Next Page", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: Button):
            if (self.current_page + 1) * 7 < len(self.leaderboard):
                self.current_page += 1
                await self.update_page(interaction)

        async def update_page(self, interaction: discord.Interaction):
            embed = discord.Embed(title="🏆 Level Leaderboard", color=discord.Color.gold())
            page = self.get_page()

            if not page:
                embed.description = "No one has progressed in levels yet."
            else:
                for i, (user_id, data) in enumerate(page, start=self.current_page * 7 + 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
                    member = interaction.guild.get_member(int(user_id))
                    if member:
                        embed.add_field(
                            name=f"{medal} {member.display_name}",
                            value=f"Level: {data['level']} | XP: {data['xp']}",
                            inline=False,
                        )
            await interaction.response.edit_message(embed=embed, view=self)

    @app_commands.command(name="leaderboard", description="View the top members by level.")
    async def leaderboard(self, interaction: discord.Interaction):
        leaderboard = sorted(
            self.levels.items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )

        view = self.LevelLeaderboard(leaderboard)
        embed = discord.Embed(title="🏆 Level Leaderboard", color=discord.Color.gold())
        
        # Display the first page
        page = view.get_page()
        if not page:
            embed.description = "No one has progressed in levels yet."
        else:
            for i, (user_id, data) in enumerate(page, start=1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
                member = interaction.guild.get_member(int(user_id))
                if member:
                    embed.add_field(
                        name=f"{medal} {member.display_name}",
                        value=f"Level: {data['level']} | XP: {data['xp']}",
                        inline=False,
                    )

        await interaction.response.send_message(embed=embed, view=view)

    # Command to reset all levels and XP
    @app_commands.command(name="reset_levels", description="Reset all levels and XP.")
    @commands.has_permissions(administrator=True)
    async def reset_levels(self, interaction: discord.Interaction):
        self.levels = {}
        self.save_data()
        await interaction.response.send_message("✅ All levels and XP have been reset.")

    # Event listener to add XP on message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = str(message.author.id)
        self.add_xp(user_id, xp=5)  # Add 5 XP per message

    # Command to add levels to a member
    @app_commands.command(name="add_level", description="Add levels to a member.")
    @commands.has_permissions(administrator=True)
    async def add_level(self, interaction: discord.Interaction, member: discord.Member, levels: int):
        user_id = str(member.id)
        user_data = self.levels.get(user_id, {"level": 1, "xp": 0})
        user_data["level"] += levels
        self.levels[user_id] = user_data
        self.save_data()
        await interaction.response.send_message(f"✅ {member.display_name} is now level {user_data['level']}.")

    # Command to remove levels from a member
    @app_commands.command(name="remove_level", description="Remove levels from a member.")
    @commands.has_permissions(administrator=True)
    async def remove_level(self, interaction: discord.Interaction, member: discord.Member, levels: int):
        user_id = str(member.id)
        user_data = self.levels.get(user_id, {"level": 1, "xp": 0})
        user_data["level"] = max(1, user_data["level"] - levels)  # Ensure level is at least 1
        self.levels[user_id] = user_data
        self.save_data()
        await interaction.response.send_message(f"✅ {member.display_name} is now level {user_data['level']}.")

    # Command to add XP to a member
    @app_commands.command(name="add_xp", description="Add XP to a member.")
    @commands.has_permissions(administrator=True)
    async def add_xp_command(self, interaction: discord.Interaction, member: discord.Member, xp: int):
        user_id = str(member.id)
        self.add_xp(user_id, xp)
        user_data = self.levels[user_id]
        await interaction.response.send_message(f"✅ {member.display_name} gained {xp} XP and is now level {user_data['level']}.")

    # Command to remove XP from a member
    @app_commands.command(name="remove_xp", description="Remove XP from a member.")
    @commands.has_permissions(administrator=True)
    async def remove_xp(self, interaction: discord.Interaction, member: discord.Member, xp: int):
        user_id = str(member.id)
        user_data = self.levels.get(user_id, {"level": 1, "xp": 0})
        user_data["xp"] = max(0, user_data["xp"] - xp)
        self.levels[user_id] = user_data
        self.save_data()
        await interaction.response.send_message(f"✅ {member.display_name} lost {xp} XP and is now level {user_data['level']}.")

    # Command to view a member's balance
    @app_commands.command(name="balance", description="View your balance or another member's balance.")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        balance = self.data.get(str(member.id), 0)
        embed = discord.Embed(
            title=f"{member.display_name}'s Balance",
            description=f"{member.mention} has **{balance} {self.currency}**.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # Command to add money to a member
    @app_commands.command(name="add_money", description="Add money to a member.")
    @commands.has_permissions(administrator=True)
    async def add_money(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ The amount must be positive.", ephemeral=True)
            return
        user_id = str(member.id)
        self.data[user_id] = self.data.get(user_id, 0) + amount
        self.save_data()
        await interaction.response.send_message(f"✅ {member.display_name} received **{amount} {self.currency}**.")

    # Command to reset the economy
    @commands.command(name="reset_economy")
    @commands.has_permissions(administrator=True)
    async def reset_economy(self, ctx):
        self.data = {}
        self.shop = []
        self.inventories = {}
        self.levels = {}
        self.save_data()
        await ctx.send("✅ The economy has been reset.")

    # Command to view the shop
    @app_commands.command(name="shop", description="View the shop.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 Shop", color=discord.Color.gold())
        if not self.shop:
            embed.description = "The shop is empty."
        else:
            for item in self.shop:
                stock = "Out of stock ❌" if item["stock"] == 0 else f"Stock: {item['stock']}"
                embed.add_field(
                    name=item["name"],
                    value=f"Price: {item['price']} {self.currency}\n{stock}",
                    inline=False
                )
        await interaction.response.send_message(embed=embed)

    # Command to buy an item from the shop
    @app_commands.command(name="buy", description="Buy an item from the shop.")
    async def buy(self, interaction: discord.Interaction, name: str, quantity: int = 1):
        user_id = str(interaction.user.id)

        if quantity <= 0:
            await interaction.response.send_message("❌ Quantity must be positive.", ephemeral=True)
            return

        for item in self.shop:
            if item["name"].lower() == name.lower():
                if item["stock"] < quantity:
                    await interaction.response.send_message(f"❌ Not enough stock for **{item['name']}**.", ephemeral=True)
                    return

                total_price = item["price"] * quantity
                if self.data.get(user_id, 0) < total_price:
                    await interaction.response.send_message(f"❌ You don't have enough money to buy **{quantity}x {item['name']}**.", ephemeral=True)
                    return

                self.data[user_id] -= total_price
                item["stock"] -= quantity

                inventory = self.inventories.get(user_id, [])
                for inv_item in inventory:
                    if inv_item["name"] == item["name"]:
                        inv_item["quantity"] += quantity
                        break
                else:
                    inventory.append({"name": item["name"], "quantity": quantity})
                self.inventories[user_id] = inventory

                self.save_data()
                await interaction.response.send_message(
                    f"✅ You bought **{quantity}x {item['name']}** for **{total_price} {self.currency}**."
                )
                return

        await interaction.response.send_message(f"❌ Item **{name}** not found in the shop.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Economy(bot))