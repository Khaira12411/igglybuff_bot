# 💗 cogs/clan/reset_clan_promo.py
import discord
from discord import app_commands
from discord.ext import commands
from asyncpg import UniqueViolationError

from utils.get_pg_pool import get_pg_pool


class ResetClanPromo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reset-clan-promo",
        description="🌸 Resets all clan promo data (USE WITH CAUTION)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_clan_promo(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        confirm_view = ConfirmResetView()
        await interaction.followup.send(
            "**⚠️ Are you sure you want to reset all clan promo data?**\n"
            "This will delete all rows from:\n"
            "`clan_promo_events`, `member_item_drops`, and `daily_item_winners`.",
            view=confirm_view,
            ephemeral=True,
        )

        timeout = await confirm_view.wait()
        if confirm_view.value is None:
            return await interaction.followup.send(
                "❌ Reset cancelled (timed out).", ephemeral=True
            )
        if not confirm_view.value:
            return await interaction.followup.send(
                "❌ Reset cancelled.", ephemeral=True
            )

        # Proceed with deletion
        pool = await get_pg_pool(self.bot)
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM clan_promo_events;")
            await conn.execute("DELETE FROM member_item_drops;")
            await conn.execute("DELETE FROM daily_item_winners;")

        await interaction.followup.send(
            "✅ All clan promo data has been reset.", ephemeral=True
        )


class ConfirmResetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


async def setup(bot):
    await bot.add_cog(ResetClanPromo(bot))
