from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.straymons.constants import *
from config.straymons.emojis import Emojis
from utils.daily_winner_db import (
    check_daily_winner_exists_for_day,
    get_daily_winner_count,
    get_top_daily_drops,
    set_daily_winner,
)
from utils.visuals.random_pink import get_random_pink

ASIA_MANILA = ZoneInfo("Asia/Manila")
START_DATE = datetime(2025, 8, 1, 12, 0, 0, tzinfo=ASIA_MANILA)
BLOCKED_WINNER_IDS = {1093841434525827142}  # Empy


class AnnounceDailyWinner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="announce-daily-winner",
        description="Manually announce daily winner(s) by day number",
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        day="Day number to announce winner(s) for (e.g., 1, 2, 3...)"
    )
    async def announce_daily_winner(self, interaction: discord.Interaction, day: int):
        await interaction.response.defer(ephemeral=True)

        if not (1 <= day <= 12):
            await interaction.followup.send("❌ Day must be between 1 and 12.")
            return

        day_start = START_DATE + timedelta(days=day - 1)
        day_end = day_start + timedelta(days=1)

        exists = await check_daily_winner_exists_for_day(self.bot, day_start.date())
        if exists:
            await interaction.followup.send(
                f"⚠️ Winner(s) for Day {day} have already been announced."
            )
            return

        top_drops = await get_top_daily_drops(self.bot)
        if not top_drops:
            await interaction.followup.send(f"❌ No drops recorded for Day {day}.")
            return

        promo_data = get_active_promo_cache()
        guild = self.bot.get_guild(STRAYMONS_GUILD_ID)
        if not guild:
            await interaction.followup.send("❌ Could not find the guild.")
            return

        sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)

        eligible_winners = []
        attempts = 0
        max_attempts = 5

        while not eligible_winners and attempts < max_attempts:
            highest_count = top_drops[0][1]
            tied_top_users = [
                (uid, cnt) for uid, cnt in top_drops if cnt == highest_count
            ]

            for user_id, count in tied_top_users:
                if user_id in BLOCKED_WINNER_IDS:
                    continue
                wins = await get_daily_winner_count(self.bot, user_id)
                if wins < 2:
                    eligible_winners.append((user_id, count))

            attempts += 1
            if not eligible_winners and len(top_drops) > 1:
                top_drops.pop(0)

        if not eligible_winners:
            await interaction.followup.send(
                "❌ No eligible winners found (all have 2+ wins or are blocked)."
            )
            return

        winner_lines = []
        for user_id, drops_count in eligible_winners:
            await set_daily_winner(
                self.bot, user_id, drops_count, winner_date=day_start.date()
            )
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)

            if sga_winner_role:
                await member.add_roles(sga_winner_role)

            wins_so_far = await get_daily_winner_count(self.bot, user_id)
            winner_lines.append(
                f"- <@{user_id}> with **{drops_count}** {promo_data['emoji_name']} {promo_data['emoji']} (Total wins: {wins_so_far})"
            )

        desc = f"""## {Emojis.pink_party} Winner(s) for Day {day}!
- {Emojis.pink_bullet} Event Name: {promo_data['name']}
- {Emojis.pink_bullet} Prize: {promo_data['prize']}

### Winners:
{chr(10).join(winner_lines)}

{Emojis.pink_paper} Notes:
- \"Please make a ticket in <#{1297255751353372825}> to claim your prize.\"
"""

        embed = discord.Embed(description=desc, color=get_random_pink())
        embed.set_image(url=promo_data["image_url"])

        news_channel = self.bot.get_channel(EVENT_NEWS_ID)
        if news_channel:
            await news_channel.send(
                f"🎉 Congratulations to the winner(s) of Day {day}!", embed=embed
            )

        logs_channel = self.bot.get_channel(REPORTS_CHANNEL_ID)
        if logs_channel:
            await logs_channel.send(
                f"📢 Announced daily winner(s) for Day {day}.", embed=embed
            )

        await interaction.followup.send(
            f"✅ Winner(s) for Day {day} announced successfully."
        )


async def setup(bot):
    await bot.add_cog(AnnounceDailyWinner(bot))
