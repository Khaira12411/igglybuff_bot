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
    get_total_plushie_drops_by_user,
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
        description="Manually announce daily winner(s) by day number",
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        day="Day number to announce winner(s) for (e.g., 1, 2, 3...)"
    )
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
                f"⚠️ Winner(s) for Day {day} have already been announced."
            )
            return

        top_drops = await get_top_daily_drops(self.bot)
        if not top_drops:
            await interaction.followup.send(f"❌ No drops recorded for Day {day}.")
            return

        BLOCKED_WINNER_IDS = {1093841434525827142}  # adjust if needed

        winners = []
        plushie_rewards = []  # fixed variable name

        for user_id, count in top_drops:
            if user_id in BLOCKED_WINNER_IDS:
                continue
            wins = await get_daily_winner_count(self.bot, user_id)
            if wins >= 2:
                continue  # Skip users with 2 or more wins already
            winners.append((user_id, count))

        if not winners:
            await interaction.followup.send(
                "❌ No eligible winners found for this day (all have 2+ wins)."
            )
            return

        guild = self.bot.get_guild(STRAYMONS_GUILD_ID)  # Replace with your guild ID
        if guild is None:
            await interaction.followup.send("❌ Could not find the guild.")
            return

        promo_data = get_active_promo_cache()
        promo_name = promo_data["name"]
        emoji = promo_data["emoji"]
        emoji_name = promo_data["emoji_name"]
        prize = promo_data["prize"]
        image_url = promo_data["image_url"]

        sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)  # No await here

        winner_lines = []
        plushie_lines = []

        for user_id, drops_count in winners:
            await set_daily_winner(
                self.bot, user_id, drops_count, winner_date=day_start.date()
            )

            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            if member is None:
                winner_lines.append(
                    f"- Unknown user ID {user_id} with {drops_count} drops"
                )
                continue

            if sga_winner_role is not None:
                await member.add_roles(sga_winner_role)

            wins_so_far = await get_daily_winner_count(self.bot, user_id)
            winner_mention = f"<@{user_id}>"
            winner_lines.append(
                f"- {winner_mention} with **{drops_count}** {emoji_name} {emoji} (Total wins: {wins_so_far})"
            )

        all_users = list({uid for uid, _ in top_drops})
        for user_id in all_users:
            if user_id in BLOCKED_WINNER_IDS:
                continue
            plushies = await get_total_plushie_drops_by_user(self.bot, user_id)
            if plushies >= 5:
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
                wins = await get_daily_winner_count(self.bot, user_id)
                reward = f"{POKECOIN_EMOJI} 100K" if wins >= 2 else prize
                plushie_rewards.append(
                    (user_id, plushies, wins, reward)
                )  # use plushies count here

        for uid, plushie_count, wins, reward in plushie_rewards:
            plushie_lines.append(
                f"- <@{uid}> got **{plushie_count} plushies** (Wins: {wins}) → {reward}"
            )

        desc = f"""## {Emojis.pink_party} Winner(s) for Day {day}!
- {Emojis.pink_bullet} Event Name: {promo_name}
- {Emojis.pink_bullet} Prize: {prize}

### Winners:
{chr(10).join(winner_lines)}
"""

        if plushie_lines:
            desc += f"""
### {Emojis.pink_trophy} Daily Plushie Rewards:
{chr(10).join(plushie_lines)}
"""

        desc += f"""
{Emojis.pink_paper} Notes:
- "Please make a ticket in <#{1297255751353372825}> to claim your prize."
"""

        embed = discord.Embed(
            description=desc,
            color=get_random_pink(),
        )
        embed.set_image(url=image_url)

        news_channel = self.bot.get_channel(EVENT_NEWS_ID)
        if news_channel:
            await news_channel.send(
                content=f"🎉 Congratulations to the winner(s) of Day {day}!",
                embed=embed,
            )

        logs_channel = self.bot.get_channel(REPORTS_CHANNEL_ID)
        if logs_channel:
            await logs_channel.send(
                f"📢 Announced daily winner(s) for Day {day}.",
                embed=embed,
            )

        await interaction.followup.send(
            f"✅ Winner(s) for Day {day} announced successfully."
        )


async def setup(bot):
    await bot.add_cog(AnnounceDailyWinner(bot))
