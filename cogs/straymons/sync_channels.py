import discord
from discord import app_commands
from discord.ext import commands

from config.straymons.constants import *


class SyncChannelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.command(
        name="sync-channels",
        description="Sync straymons_channels into straymons_members (import and update all data)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_channels(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.bot.pg_pool.acquire() as conn:
            channels_rows = await conn.fetch(
                "SELECT user_id, channel_id FROM straymons_channels"
            )

            if not channels_rows:
                await interaction.followup.send(
                    "No data found in straymons_channels to sync.", ephemeral=True
                )
                return

            await conn.executemany(
                """
                INSERT INTO straymons_members (user_id, channel_id)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET channel_id = EXCLUDED.channel_id
                """,
                [(row["user_id"], row["channel_id"]) for row in channels_rows],
            )

            await interaction.followup.send(
                f"Synced {len(channels_rows)} entries from straymons_channels to straymons_members.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(SyncChannelsCog(bot))
