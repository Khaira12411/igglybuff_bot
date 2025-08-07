from datetime import datetime, timedelta
from typing import List, Tuple
from zoneinfo import ZoneInfo

import discord

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.straymons.constants import HUNT_CHANNEL_ID, POKECOIN_EMOJI
from config.straymons.dividers import DividerImages
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
prize_1 = f"{Emojis.golden} Gardevoir + 10M {Emojis.pokecoin}"
prize_2 = f"{Emojis.golden} Diancie + 5M {Emojis.pokecoin}"
prize_3 = f"{Emojis.golden} Keldeo + 2.5M {Emojis.pokecoin}"


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
    promo_data = get_active_promo_cache()

    try:
        #
        if current_day_number > 12:
            top_finalists = await get_top_drops_in_range(bot=bot, days=12)

            if not top_finalists:
                iggly_log(
                    "skip", "No top drops found for final winners.", label="DailyWinner"
                )
                return

            channel = bot.get_channel(EVENT_NEWS_ID)
            if not channel:
                iggly_log(
                    "critical",
                    "Announcement channel not found.",
                    label="DailyWinner",
                    bot=bot,
                )
                return

            guild = channel.guild
            sga_winner_role = guild.get_role(SGA_WINNER_ROLE_ID)

            final_announcement = f"""## {Emojis.pink_star} Final Winners for **{promo_data['name']}**!
{Emojis.pink_bullet} Total range: Last 12 days
{Emojis.pink_bullet} Top 3 plushie droppers:
"""

            for idx, (user_id, total) in enumerate(top_finalists, start=1):
                prize = {
                    1: f"🏆 1st Prize: {prize_1}",
                    2: f"🥈 2nd Prize: {prize_2}",
                    3: f"🥉 3rd Prize: {prize_3}",
                }.get(idx, "🎁 Participation Prize")

                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
                if member and sga_winner_role:
                    await member.add_roles(sga_winner_role)
                    iggly_log(
                        "sent",
                        f"SGA Winner role given to {user_id}",
                        label="FinalWinners",
                    )

                    try:
                        await member.send(
                            f"🎉 Congrats! You placed **#{idx}** in the **{promo_data['name']}** event!\n"
                            f"You won: {prize}\n\nPlease make a ticket in <#{1297255751353372825}> to claim your reward!"
                        )
                        iggly_log(
                            "dm",
                            f"Sent DM to {user_id} (Rank {idx})",
                            label="FinalWinners",
                        )
                    except Exception as e:
                        iggly_log(
                            "error",
                            f"Failed to DM user {user_id}: {e}",
                            label="FinalWinners",
                        )

                final_announcement += (
                    f"- <@{user_id}> with **{total} plushies** → {prize}\n"
                )

            embed = discord.Embed(
                title=f"🎉 Final Top 3 Winners — {promo_data['name']}!",
                description=final_announcement,
                color=get_random_pink(),
            )
            embed.set_image(url=DividerImages.Pink_Clouds)
            await channel.send(embed=embed)
            iggly_log("sent", "Final winners announcement sent.", label="FinalWinners")

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
        iggly_log("db", f"Promo data fetched: {promo_data}", label="DailyWinner")
        prize = promo_data["prize"]

        # ✨ Plushie earners block
        plushie_earners = [(uid, count) for uid, count in top_drops if count >= 5]
        plushie_rewards = []
        for user_id, count in plushie_earners:
            if user_id in BLOCKED_WINNER_IDS:
                continue
            wins = await get_daily_winner_count(bot, user_id)
            reward = f"{POKECOIN_EMOJI} 100K" if wins >= 2 else prize
            plushie_rewards.append((user_id, count, wins, reward))

        channel = bot.get_channel(announcement_channel_id)
        if not channel:
            iggly_log(
                "critical",
                "Announcement channel not found. Exiting.",
                label="DailyWinner",
                bot=bot,
            )
            return

        sga_winner_role = channel.guild.get_role(SGA_WINNER_ROLE_ID)

        announcement_lines = []
        for user_id, count, wins, reward in plushie_rewards:
            await set_daily_winner(bot, user_id, count, winner_date=day_start.date())
            iggly_log(
                "db",
                f"Plushie earner {user_id} logged as daily winner",
                label="DailyWinner",
            )

            if reward != f"{POKECOIN_EMOJI} 100K":
                member = channel.guild.get_member(
                    user_id
                ) or await channel.guild.fetch_member(user_id)
                if sga_winner_role and member:
                    await member.add_roles(sga_winner_role)
                    iggly_log(
                        "sent",
                        f"SGA Winner role given to {user_id}",
                        label="DailyWinner",
                    )

            announcement_lines.append(
                f"<@{user_id}> with **{count}** plushies {promo_data['emoji']} (Wins: {wins})"
            )

        # Send combined announcement for all winners
        desc = f"""## {Emojis.pink_party} Winner(s) for Day {current_day_number}!
{Emojis.pink_bullet} Event Name: {promo_data['name']}
{Emojis.pink_bullet} Prize: {promo_data['prize']}

{Emojis.pink_bullet} Congratulations to:
"""
        desc += "\n".join(f"- {line}" for line in announcement_lines)

        if plushie_rewards:
            desc += f"\n\n{Emojis.pink_gift} **Daily Plushie Rewards:**\n"
            for uid, count, wins, reward in plushie_rewards:
                desc += (
                    f"- <@{uid}> got **{count} plushies** (Wins: {wins}) → {reward}\n"
                )

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
        content = f"# ˗ˏˋ ୨💖୧ ˎˊ˗ ⊹🌸⊹ ୨ Day {new_day} ୧ ⊹🌸⊹ ˗ˏˋ ୨💖୧ ˎˊ˗"
        await hunt_channel.send(content=content)

    except Exception as e:
        iggly_log(
            "critical",
            f"Unexpected error during winner announcement: {e}",
            label="DailyWinner",
            bot=bot,
            include_trace=True,
        )
