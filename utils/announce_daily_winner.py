from datetime import datetime, timedelta
from typing import List, Tuple
from zoneinfo import ZoneInfo

import discord

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.straymons.emojis import Emojis
from utils.daily_winner_db import *
from utils.time import *

BLOCKED_WINNER_IDS = {
    1093841434525827142,  # Empy
}

ASIA_MANILA = ZoneInfo("Asia/Manila")  # 🕒 Timezone constant for Asia/Manila
from config.straymons.constants import *
from utils.visuals.random_pink import get_random_pink

START_DATE = datetime(2025, 8, 1, 12, 0, 0, tzinfo=ASIA_MANILA)  # Event start date


async def announce_daily_winner(bot: discord.Client):
    announcement_channel_id = EVENT_NEWS_ID

    now = datetime.now(tz=ASIA_MANILA)
    current_day_number = (now - START_DATE).days + 1

    if current_day_number > 12:
        # Event ended — announce top 3 overall winners instead
        print(f"[Daily Winner] Event ended, announcing top 3 overall winners.")

        top_overall = await get_top_drops_in_range(bot, days=12)
        if not top_overall:
            print("[Daily Winner] No overall drops recorded.")
            return

        channel = bot.get_channel(announcement_channel_id)
        if not channel:
            print("[Daily Winner] Announcement channel not found.")
            return

        promo_data = get_active_promo_cache()
        promo_name = promo_data["name"]
        image_url = promo_data["image_url"]
        emoji = promo_data["emoji"]
        emoji_name = promo_data["emoji_name"]
        prize = promo_data["prize"]

        embed = discord.Embed(
            title=f"🎉 Final Top 3 {promo_name} Winners!",
            description="Here are the top 3 winners with the most drops over the entire event:",
            color=get_random_pink(),
        )
        for rank, (user_id, count) in enumerate(top_overall, start=1):
            guild = channel.guild
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            embed.add_field(
                name=f"#{rank} — {member.display_name}",
                value=f"{count} {emoji_name} {emoji}",
                inline=False,
            )
            # Optionally add roles here if you want

        embed.set_image(url=image_url)
        await channel.send(embed=embed)

        return  # Do not continue with daily winner logic after event ends

    # Before event end, announce daily winners as usual
    day_start, day_end = get_day_range_by_index(START_DATE, current_day_number)

    print(f"[Daily Winner] Current Day {current_day_number} — {day_start} to {day_end}")

    # 📊 Get top drops within current day range
    top_drops = await get_top_daily_drops(bot, day_start, day_end)
    if not top_drops:
        print("[Daily Winner] No drops recorded for this day.")
        return

    # 🏆 Find winner logic (same as before)...
    winner_id = None
    drops_count = None

    promo_data = get_active_promo_cache()
    promo_name = promo_data["name"]
    image_url = promo_data["image_url"]
    emoji = promo_data["emoji"]
    emoji_name = promo_data["emoji_name"]
    prize = promo_data["prize"]

    for user_id, count in top_drops:
        if user_id in BLOCKED_WINNER_IDS:
            print(f"[Daily Winner] Skipping blocked user {user_id}")
            continue

        wins = await get_daily_winner_count(bot, user_id)
        if wins < 2:
            winner_id = user_id
            drops_count = count
            break

    if winner_id is None:
        print("[Daily Winner] No eligible winner found.")
        return

    await set_daily_winner(bot, winner_id, drops_count, winner_date=day_start.date())

    # 📣 Send announcement embed
    channel = bot.get_channel(announcement_channel_id)
    if not channel:
        print("[Daily Winner] Announcement channel not found.")
        return

    guild = channel.guild
    sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)
    member = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
    await member.add_roles(sga_winner_role)

    winner_mention = f"<@{winner_id}>"
    content = f"Congratulations {winner_mention}, You've won a {prize}!"
    desc = f"""## {Emojis.pink_party} Winner for Day {current_day_number}!
- {Emojis.pink_bullet} Event Name: {promo_name}
- {Emojis.pink_bullet} Winner: {winner_mention}
- {Emojis.pink_bullet} Total Drops: **{drops_count}** {emoji_name} {emoji}
- {Emojis.pink_bullet} Prize: {prize}
- {Emojis.pink_bullet} Total Number of Wins: {wins}

{Emojis.pink_paper} Notes:
- "Please make a ticket in <#{1297255751353372825}> to claim your prize."""
    embed = discord.Embed(
        title=f"🎉 Daily {promo_name} Winner for Day {current_day_number}!",
        description=desc,
        color=get_random_pink(),
    )
    embed.set_image(url=image_url)
    await channel.send(content=content, embed=embed)

    # ✅ Only now, roll over to the next day
    await increment_day_number(bot)
    print(f"[Daily Winner] Rolled over to Day {current_day_number + 1}.")
