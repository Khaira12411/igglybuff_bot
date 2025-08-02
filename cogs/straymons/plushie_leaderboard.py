from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.guild_ids import STRAYMONS_GUILD_ID
from config.straymons.constants import STAFF_ROLE_ID
from utils.daily_winner_db import get_top_daily_drops, get_top_drops_in_range

ASIA_MANILA = ZoneInfo("Asia/Manila")
STAFF_ROLE_ID = STAFF_ROLE_ID  # 🔐 Replace with your actual staff role ID


def get_reset_time_note():
    now = datetime.now(tz=ASIA_MANILA)
    # Calculate next reset time (12 PM today or tomorrow if past 12 PM)
    reset_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now >= reset_time:
        reset_time += timedelta(days=1)
    # Format nicely for user display, e.g. "Aug 2, 12:00 PM"
    formatted = reset_time.strftime("%b %d, %I:%M %p")
    return f"*Stats reset at {formatted} Asia/Manila*"


def get_reset_time_note():
    now = datetime.now(tz=ASIA_MANILA)
    reset_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now >= reset_time:
        reset_time += timedelta(days=1)
    unix_ts = int(reset_time.timestamp())
    # Format with Discord's timestamp markdown, showing absolute and relative time
    return f"Stats reset <t:{unix_ts}:f> (<t:{unix_ts}:R>) Asia/Manila"


class PlushieLeaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="plushie-leaderboard", description="💖 View top plushie collectors!"
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.describe(
        timeframe="Choose 'All Time' or 'Today' to view the leaderboard type"
    )
    @app_commands.choices(
        timeframe=[
            app_commands.Choice(name="All Time", value="all_time"),
            app_commands.Choice(name="Today", value="today"),
        ]
    )
    async def plushie_leaderboard(
        self,
        interaction: discord.Interaction,
        timeframe: app_commands.Choice[str],
    ):
        if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "❌ You don’t have permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        promo_data = get_active_promo_cache()
        title_promo = promo_data["name"]
        image_url = promo_data["image_url"]
        emoji = promo_data["emoji"]
        emoji_name = promo_data["emoji_name"]

        if timeframe.value == "today":
            now = datetime.now(ASIA_MANILA)
            top_drops = await get_top_daily_drops(self.bot, now)
            title = "🌸 Today's Top Plushie Collectors"
            reset_note = get_reset_time_note()
        else:
            top_drops = await get_top_drops_in_range(self.bot)
            title = "🌷 All-Time Top Plushie Collectors (Past 12 Days)"
            reset_note = None  # No reset note for all-time

        if not top_drops:
            await interaction.followup.send(
                "No plushie drops found yet! 🥺", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=title,
            color=discord.Color.from_str("#FFB6C1"),  # Light Pink
            description="Here's who’s been gathering the fluffiest finds!",
        )
        embed.set_thumbnail(url=interaction.guild.icon.url)

        for idx, (user_id, count) in enumerate(top_drops, start=1):
            user = interaction.guild.get_member(user_id)
            display_name = user.display_name if user else f"<User {user_id}>"
            name = user.mention if user else f"<User {user_id}>"
            embed.add_field(
                name=f"#{idx} {display_name}",
                value=f"> - **{count} {emoji_name}** {emoji}",
                inline=False,
            )

        if reset_note:
            embed.add_field(
                name="\u200b",
                value=f"{reset_note}",
                inline=False,
            )

        embed.set_footer(
            text="Keep spreading the fluff 💗",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )
        embed.set_author(name=f"For {title_promo}", icon_url=interaction.guild.icon.url)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PlushieLeaderboard(bot))
