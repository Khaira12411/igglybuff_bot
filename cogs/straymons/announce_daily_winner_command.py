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
START_DATE = datetime(2025, 8, 1, 12, 0, 0, tzinfo=ASIA_MANILA)  # Adjust as needed


class AnnounceDailyWinner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner():
        async def predicate(interaction: discord.Interaction) -> bool:
            return await interaction.client.is_owner(interaction.user)

        return app_commands.check(predicate)

    @app_commands.command(
        name="announce-daily-winner",
        description="Manually announce daily winner by day number",
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(day="Day number to announce winner for (e.g., 1, 2, 3...)")
    async def announce_daily_winner(self, interaction: discord.Interaction, day: int):
        await interaction.response.defer(ephemeral=True)

        if day < 1 or day > 12:
            await interaction.followup.send("❌ Day must be between 1 and 12.")
            return

        day_start = START_DATE + timedelta(days=day - 1)
        day_end = day_start + timedelta(days=1)

        exists = await check_daily_winner_exists_for_day(self.bot, day_start.date())
        if exists:
            await interaction.followup.send(
                f"⚠️ Winner for Day {day} has already been announced."
            )
            return

        top_drops = await get_top_daily_drops(self.bot)
        if not top_drops:
            await interaction.followup.send(f"❌ No drops recorded for Day {day}.")
            return

        BLOCKED_WINNER_IDS = {1093841434525827142}  # adjust if needed

        winner_id = None
        drops_count = None

        for user_id, count in top_drops:
            if user_id in BLOCKED_WINNER_IDS:
                continue
            wins = await get_daily_winner_count(self.bot, user_id)
            if wins >= 2:
                continue  # Skip users with 2 or more wins already
            winner_id = user_id
            drops_count = count
            break

        if winner_id is None:
            await interaction.followup.send(
                "❌ No eligible winner found for this day (all winners have 2+ wins)."
            )
            return

        await set_daily_winner(
            self.bot, winner_id, drops_count, winner_date=day_start.date()
        )

        guild = self.bot.get_guild(STRAYMONS_GUILD_ID)  # Replace with your guild ID
        if guild is None:
            await interaction.followup.send("❌ Could not find the guild.")
            return

        member = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
        if member is None:
            await interaction.followup.send("❌ Winner not found in the guild.")
            return

        wins_so_far = await get_daily_winner_count(self.bot, winner_id)

        promo_data = get_active_promo_cache()
        promo_name = promo_data["name"]
        emoji = promo_data["emoji"]
        emoji_name = promo_data["emoji_name"]
        prize = promo_data["prize"]
        image_url = promo_data["image_url"]

        sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)  # No await here
        if sga_winner_role is not None:
            await member.add_roles(sga_winner_role)

        winner_mention = f"<@{winner_id}>"
        desc = f"""## {Emojis.pink_party} Winner for Day {day}!
- {Emojis.pink_bullet} Event Name: {promo_name}
- {Emojis.pink_bullet} Winner: {winner_mention}
- {Emojis.pink_bullet} Total Drops: **{drops_count}** {emoji_name} {emoji}
- {Emojis.pink_bullet} Prize: {prize}
- {Emojis.pink_bullet} Total Number of Wins: {wins_so_far}

{Emojis.pink_paper} Notes:
- "Please make a ticket in <#{1297255751353372825}> to claim your prize."""

        embed = discord.Embed(
            description=desc,
            color=get_random_pink(),
        )
        embed.set_image(url=image_url)
        embed.set_thumbnail(url=member.display_avatar.url)

        news_channel = self.bot.get_channel(EVENT_NEWS_ID)
        if news_channel:
            await news_channel.send(
                content=f"Congratulations {winner_mention}, you've won a {prize}!",
                embed=embed,
            )

        logs_channel = self.bot.get_channel(REPORTS_CHANNEL_ID)
        if logs_channel:
            await logs_channel.send(
                f"📢 Announced daily winner for Day {day}: {member.display_name} ({winner_id}) with {drops_count} drops.",
                embed=embed,
            )

        await interaction.followup.send(
            f"✅ Winner for Day {day} announced successfully."
        )


async def setup(bot):
    await bot.add_cog(AnnounceDailyWinner(bot))
