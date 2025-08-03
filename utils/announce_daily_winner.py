from datetime import datetime, timedelta
from typing import List, Tuple
from zoneinfo import ZoneInfo

import discord

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.straymons.constants import HUNT_CHANNEL_ID
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
    print("[Daily Winner] Starting daily winner announcement...")

    now = datetime.now(tz=ASIA_MANILA)
    current_day_number = (now - START_DATE).days + 1
    print(f"[Daily Winner] Current datetime: {now.isoformat()}")
    print(f"[Daily Winner] Calculated current_day_number: {current_day_number}")

    if current_day_number > 12:
        print(f"[Daily Winner] Event ended, announcing top 3 overall winners.")

        top_overall = await get_top_drops_in_range(bot, days=12)
        if not top_overall:
            print("[Daily Winner] No overall drops recorded. Exiting.")
            return
        hunt_channel = bot.get_channel(HUNT_CHANNEL_ID)
        channel = bot.get_channel(announcement_channel_id)
        if not channel:
            print("[Daily Winner] Announcement channel not found. Exiting.")
            return

        promo_data = get_active_promo_cache()
        print(f"[Daily Winner] Promo data fetched: {promo_data}")

        embed = discord.Embed(
            title=f"🎉 Final Top 3 {promo_data['name']} Winners!",
            description="Here are the top 3 winners with the most drops over the entire event:",
            color=get_random_pink(),
        )

        for rank, (user_id, count) in enumerate(top_overall, start=1):
            guild = channel.guild
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            print(
                f"[Daily Winner] Adding rank #{rank}: {member.display_name} with {count} drops"
            )
            embed.add_field(
                name=f"#{rank} — {member.display_name}",
                value=f"{count} {promo_data['emoji_name']} {promo_data['emoji']}",
                inline=False,
            )

        embed.set_image(url=promo_data["image_url"])
        await channel.send(embed=embed)
        print("[Daily Winner] Final top 3 announcement sent.")
        return

    # Event ongoing, announce daily winner
    day_start, day_end = get_day_range_by_index(START_DATE, current_day_number)
    print(f"[Daily Winner] Current Day {current_day_number} — {day_start} to {day_end}")

    top_drops = await get_top_daily_drops(bot)
    if not top_drops:
        print("[Daily Winner] No drops recorded for this day. Exiting.")
        return

    print(f"[Daily Winner] Top drops fetched: {top_drops}")

    winner_id = None
    drops_count = None

    promo_data = get_active_promo_cache()
    print(f"[Daily Winner] Promo data fetched: {promo_data}")

    for user_id, count in top_drops:
        if user_id in BLOCKED_WINNER_IDS:
            print(f"[Daily Winner] Skipping blocked user {user_id}")
            continue

        wins = await get_daily_winner_count(bot, user_id)
        print(f"[Daily Winner] User {user_id} has won {wins} times before")

        if wins < 2:
            winner_id = user_id
            drops_count = count
            print(
                f"[Daily Winner] Selected winner: {winner_id} with {drops_count} drops"
            )
            break

    if winner_id is None:
        print("[Daily Winner] No eligible winner found. Exiting.")
        return

    await set_daily_winner(bot, winner_id, drops_count, winner_date=day_start.date())
    print(f"[Daily Winner] Winner {winner_id} recorded for day {current_day_number}")

    channel = bot.get_channel(announcement_channel_id)
    if not channel:
        print("[Daily Winner] Announcement channel not found. Exiting.")
        return

    guild = channel.guild
    sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)
    member = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
    await member.add_roles(sga_winner_role)
    print(f"[Daily Winner] Role {SGA_WINNER_ROLE_ID} assigned to winner {winner_id}")

    winner_mention = f"<@{winner_id}>"
    content = f"Congratulations {winner_mention}, You've won a {promo_data['prize']}!"
    desc = f"""## {Emojis.pink_party} Winner for Day {current_day_number}!
- {Emojis.pink_bullet} Event Name: {promo_data['name']}
- {Emojis.pink_bullet} Winner: {winner_mention}
- {Emojis.pink_bullet} Total Drops: **{drops_count}** {promo_data['emoji_name']} {promo_data['emoji']}
- {Emojis.pink_bullet} Prize: {promo_data['prize']}
- {Emojis.pink_bullet} Total Number of Wins: {wins}

{Emojis.pink_paper} Notes:
- "Please make a ticket in <#{1297255751353372825}> to claim your prize."""
    embed = discord.Embed(
        title=f"🎉 Daily {promo_data['name']} Winner for Day {current_day_number}!",
        description=desc,
        color=get_random_pink(),
    )
    embed.set_image(url=promo_data["image_url"])
    await channel.send(content=content, embed=embed)
    print("[Daily Winner] Announcement sent successfully.")

    await increment_day_number(bot)
    print(f"[Daily Winner] Rolled over to Day {current_day_number + 1}.")
    new_day = current_day_number + 1

    hunt_channel = bot.get_channel(HUNT_CHANNEL_ID)
    content = (
        f"# ────────────── ˖ ݁𖥔 ݁˖ 🩷 ˖ ݁𖥔 ݁˖ NEW {new_day} ˖ ݁𖥔 ݁˖ 🩷 ˖ ݁𖥔 ݁˖ ──────────────"
    )
    await hunt_channel.send(content=content)
