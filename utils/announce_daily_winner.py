from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import discord

from cogs.promo_refresher import get_active_promo_cache
from utils.daily_winner_db import (  # This function should return how many times a user has won; 📥 Import DB functions for drops and winner
    get_daily_winner_count,
    get_top_daily_drops,
    set_daily_winner,
)

ASIA_MANILA = ZoneInfo("Asia/Manila")  # 🕒 Timezone constant for Asia/Manila
from utils.visuals.random_pink import get_random_pink
from config.constants import *

# ————————————————————————————————
# 🎉 announce_daily_winner – Sends daily winner announcement embed and saves winner
# ————————————————————————————————
async def announce_daily_winner(bot: discord.Client):
    # ⏰ Get previous day date and midnight time with timezone
    
    announcement_channel_id = EVENT_NEWS_ID

    now = datetime.now(tz=ASIA_MANILA)
    previous_day = (now - timedelta(days=1)).date()
    day_start = datetime.combine(previous_day, time.min, tzinfo=ASIA_MANILA)

    # 📊 Fetch top daily drops sorted descending (list of tuples (user_id, drops_count))
    top_drops = await get_top_daily_drops(bot, day_start)
    if not top_drops:
        print("[Daily Winner] No drops recorded yesterday.")
        return

    winner_id = None
    drops_count = None

    # 🌸 Get current active promo
    promo_data = get_active_promo_cache()
    print(f"[DEBUG] Promo data from cache: {promo_data}")

    # 📝 Promo info
    promo_name = promo_data["name"]
    image_url = promo_data["image_url"]
    emoji = promo_data["emoji"]
    emoji_name = promo_data["emoji_name"]
    catch_rate = promo_data["catch_rate"]
    fish_rate = promo_data["fish_rate"]
    battle_rate = promo_data["battle_rate"]
    prize = promo_data["prize"]

    # 🛑 Skip users who already won 2 or more times, find next eligible
    for user_id, count in top_drops:
        wins = await get_daily_winner_count(bot, user_id)
        if wins < 2:
            winner_id = user_id
            drops_count = count
            break

    if winner_id is None:
        print("[Daily Winner] No eligible winner found (all have won 2+ times).")
        return

    # 💾 Save the daily winner info to the database
    await set_daily_winner(bot, winner_id, drops_count, winner_date=previous_day)

    # 📣 Fetch announcement channel
    channel = bot.get_channel(announcement_channel_id)
    if not channel:
        print("[Daily Winner] Announcement channel not found.")
        return

    # 🎖️ Assign reward role to winner
    guild = channel.guild
    sga_winner_role_id = SGA_WINNER_ROLE_ID  # 📝 Replace with the actual reward role ID
    sga_winner_role = guild.get_role(sga_winner_role_id)
    member = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
    await member.add_roles(sga_winner_role)

    # 🏆 Prepare and send the winner embed message
    content = f"Congratulations {winner_mention}, You've won a {prize}!"
    winner_mention = f"<@{winner_id}>"
    embed = discord.Embed(
        title=f"🎉 Daily {promo_name} Winner for {previous_day.strftime('%B %d, %Y')}!",
        description=(
            f"Congratulations to {winner_mention} for having the most drops yesterday "
            f"with **{drops_count}** {emoji_name} {emoji}\n"
            f"Please make a ticket in <#{1297255751353372825}>, and wait for Skaia to hand over your prize!"
        ),
        color=get_random_pink(),
    )
    embed.set_image(url=image_url)
    await channel.send(content=content, embed=embed)
