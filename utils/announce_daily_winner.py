from datetime import datetime, timedelta
from typing import List, Tuple
from zoneinfo import ZoneInfo

import discord

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.straymons.constants import HUNT_CHANNEL_ID
from config.straymons.emojis import Emojis
from utils.daily_winner_db import *
from utils.time import *
from utils.visuals.iggly_log_helpers import iggly_log  # 💖 Logging for Iggly

BLOCKED_WINNER_IDS = {
    1093841434525827142,  # Empy
}

ASIA_MANILA = ZoneInfo("Asia/Manila")  # 🕒 Timezone constant for Asia/Manila
from config.straymons.constants import *
from utils.visuals.random_pink import get_random_pink

START_DATE = datetime(2025, 8, 1, 12, 0, 0, tzinfo=ASIA_MANILA)  # Event start date


async def announce_daily_winner(bot: discord.Client):
    announcement_channel_id = EVENT_NEWS_ID
    iggly_log("ready", "Starting daily winner announcement...", label="DailyWinner")

    now = datetime.now(tz=ASIA_MANILA)
    current_day_number = (now - START_DATE).days + 1
    iggly_log(
        "ready",
        f"Current datetime: {now.isoformat()}\nCalculated current_day_number: {current_day_number}",
        label="DailyWinner",
    )

    try:
        if current_day_number > 12:
            # (Unchanged - final top 3 announcement block)
            return

        # Event ongoing, announce daily winner(s)
        day_start, day_end = get_day_range_by_index(START_DATE, current_day_number)
        iggly_log(
            "ready",
            f"Current Day {current_day_number} — {day_start} to {day_end}",
            label="DailyWinner",
        )

        top_drops = await get_top_daily_drops(bot)
        if not top_drops:
            iggly_log(
                "skip", "No drops recorded for this day. Exiting.", label="DailyWinner"
            )
            return

        iggly_log("db", f"Top drops fetched: {top_drops}", label="DailyWinner")
        promo_data = get_active_promo_cache()
        iggly_log("db", f"Promo data fetched: {promo_data}", label="DailyWinner")

        # --- Start multi-winner support with limited attempts ---
        highest_count = top_drops[0][1]
        tied_top_users = [(uid, cnt) for uid, cnt in top_drops if cnt == highest_count]

        eligible_winners = []
        max_attempts = 5
        attempts = 0

        for user_id, count in tied_top_users:
            if attempts >= max_attempts:
                break
            attempts += 1

            if user_id in BLOCKED_WINNER_IDS:
                iggly_log(
                    "skip", f"Skipping blocked user {user_id}", label="DailyWinner"
                )
                continue

            wins = await get_daily_winner_count(bot, user_id)
            iggly_log(
                "db", f"User {user_id} has won {wins} times before", label="DailyWinner"
            )

            if wins < 2:
                eligible_winners.append((user_id, count))

        if not eligible_winners:
            iggly_log(
                "skip",
                "No eligible winners found after 5 attempts.",
                label="DailyWinner",
            )
            return

        channel = bot.get_channel(announcement_channel_id)
        if not channel:
            iggly_log(
                "critical",
                "Announcement channel not found. Exiting.",
                label="DailyWinner",
                bot=bot,
            )
            return

        guild = channel.guild
        sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)

        announcement_lines = []
        for winner_id, drops_count in eligible_winners:
            await set_daily_winner(
                bot, winner_id, drops_count, winner_date=day_start.date()
            )
            iggly_log(
                "db",
                f"Winner {winner_id} recorded for day {current_day_number}",
                label="DailyWinner",
            )

            member = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
            await member.add_roles(sga_winner_role)
            iggly_log(
                "sent",
                f"Role {SGA_WINNER_ROLE_ID} assigned to winner {winner_id}",
                label="DailyWinner",
            )

            winner_mention = f"<@{winner_id}>"
            wins = await get_daily_winner_count(bot, winner_id)
            announcement_lines.append(
                f"{winner_mention} with **{drops_count}** {promo_data['emoji_name']} {promo_data['emoji']} (Total wins: {wins})"
            )

        desc = f"""## {Emojis.pink_party} Winner(s) for Day {current_day_number}!
- {Emojis.pink_bullet} Event Name: {promo_data['name']}
- {Emojis.pink_bullet} Prize: {promo_data['prize']}

{Emojis.pink_bullet} Congratulations to:
"""
        desc += "\n".join(f"- {line}" for line in announcement_lines)
        desc += f"""

{Emojis.pink_paper} Notes:
- \"Please make a ticket in <#{1297255751353372825}> to claim your prize.\"
"""

        embed = discord.Embed(
            title=f"🎉 Daily {promo_data['name']} Winner(s) for Day {current_day_number}!",
            description=desc,
            color=get_random_pink(),
        )
        embed.set_image(url=promo_data["image_url"])
        await channel.send(embed=embed)
        iggly_log("sent", "Announcement sent successfully.", label="DailyWinner")

        await increment_day_number(bot)
        new_day = await get_current_day_number(bot=bot)
        iggly_log("db", f"Rolled over to Day {new_day}.", label="DailyWinner")

        hunt_channel = bot.get_channel(HUNT_CHANNEL_ID)
        content = f"# ───────────────── ˖ ݑ🕔 ݑ˖ 🦥 ˖ ݑ🕔 ݑ˖ NEW {new_day} ˖ ݑ🕔 ݑ˖ 🦥 ˖ ݑ🕔 ݑ˖ ─────────────────"
        await hunt_channel.send(content=content)

    except Exception as e:
        iggly_log(
            "critical",
            f"Unexpected error during winner announcement: {e}",
            label="DailyWinner",
            bot=bot,
            include_trace=True,
        )
