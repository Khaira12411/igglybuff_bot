from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import discord

from utils.visuals.iggly_log_helpers import iggly_log  # 💖 Logging for Iggly

# 💖 Asia Manila timezone for all date/time operations
ASIA_MANILA = ZoneInfo("Asia/Manila")

# ╭──────────────────────────────────────────────╮
# 💗 DAILY WINNER MANAGEMENT
# ╰──────────────────────────────────────────────╯


# 💖 Insert or update the daily winner record
async def set_daily_winner(
    bot,
    user_id: int,
    total_drops: int,
    winner_date: Optional[date] = None,
):
    if winner_date is None:
        winner_date = date.today()

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO daily_item_winners (winner_date, user_id, total_drops, recorded_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (winner_date, user_id) DO UPDATE SET
                total_drops = EXCLUDED.total_drops,
                recorded_at = NOW()
            """,
            winner_date,
            user_id,
            total_drops,
        )
        iggly_log(
            "db",
            f"Set daily winner {user_id} with {total_drops} drops for {winner_date}",
            bot=bot,
        )


# 💖 Retrieve daily winner info for a specific date (default: today)
async def get_daily_winner(bot, winner_date: Optional[date] = None) -> Optional[Dict]:
    if winner_date is None:
        winner_date = date.today()

    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_item_winners WHERE winner_date = $1",
            winner_date,
        )
        iggly_log("db", f"Fetched winner for {winner_date}: {row}", bot=bot)
        return dict(row) if row else None


# 💖 Fetch all daily winners ordered by most recent first
async def get_all_winners(bot) -> List[Dict]:
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM daily_item_winners ORDER BY winner_date DESC"
        )
        iggly_log("db", f"Fetched {len(rows)} total winner records.", bot=bot)
        return [dict(row) for row in rows]


# 💖 Clear all daily winner records from the table
async def clear_daily_winners(bot):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute("DELETE FROM daily_item_winners")
        iggly_log("db", "Cleared all records from daily_item_winners table.", bot=bot)


# ╭──────────────────────────────────────────────╮
# 💗 RANGE + TIME UTILITY
# ╰──────────────────────────────────────────────╯


def get_12pm_day_ranges(
    start_date: datetime, num_days: int, tz
) -> List[Tuple[datetime, datetime]]:
    base = start_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=tz)
    ranges = []
    for i in range(num_days):
        day_start = base + timedelta(days=i)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        ranges.append((day_start, day_end))
    return ranges


# ╭──────────────────────────────────────────────╮
# 💗 DROP STATS TRACKING
# ╰──────────────────────────────────────────────╯


# 💖 Get top daily drops for a specific day in Asia/Manila timezone
async def get_top_daily_drops(bot) -> List[Tuple[int, int]]:
    async with bot.pg_pool.acquire() as conn:
        current_day_row = await conn.fetchrow(
            "SELECT day_number FROM current_day LIMIT 1;"
        )
        if not current_day_row:
            return []

        day_number = current_day_row["day_number"]

        rows = await conn.fetch(
            """
            SELECT user_id, COUNT(*) AS drops_count
            FROM member_item_drops
            WHERE day = $1
            GROUP BY user_id
            ORDER BY drops_count DESC;
            """,
            day_number,
        )
        iggly_log("db", f"Fetched top daily drops for day {day_number}.", bot=bot)
        return [(r["user_id"], r["drops_count"]) for r in rows]


# 💖 Get top 3 users with most drops over the last `days` days
async def get_top_drops_in_range(bot, days: int = 12) -> List[Tuple[int, int]]:
    now = datetime.now(tz=ASIA_MANILA)
    start = now - timedelta(days=days)

    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, COUNT(*) AS total_drops
            FROM member_item_drops
            WHERE drop_time >= $1 AND drop_time <= $2
            GROUP BY user_id
            ORDER BY total_drops DESC
            LIMIT 3;
            """,
            start,
            now,
        )
        iggly_log(
            "db",
            f"Fetched top 3 drops in range {start.date()} to {now.date()}.",
            bot=bot,
        )
        return [(r["user_id"], r["total_drops"]) for r in rows]


# ╭──────────────────────────────────────────────╮
# 💗 MISC UTILITIES
# ╰──────────────────────────────────────────────╯


async def get_daily_winner_count(bot: discord.Client, user_id: int) -> int:
    query = "SELECT COUNT(*) FROM daily_item_winners WHERE user_id = $1"
    async with bot.pg_pool.acquire() as conn:
        count = await conn.fetchval(query, user_id)
    iggly_log("db", f"Winner count for user {user_id}: {count}", bot=bot)
    return count or 0


async def get_current_day_number(bot) -> int:
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT day_number FROM current_day LIMIT 1;")
        num = row["day_number"] if row else 1
        iggly_log("db", f"Fetched current day number: {num}", bot=bot)
        return num


async def increment_day_number(bot):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE current_day SET day_number = day_number + 1, last_updated = now();"
        )
        iggly_log("db", "Incremented day number in current_day.", bot=bot)


async def check_daily_winner_exists_for_day(bot, winner_date: date) -> bool:
    async with bot.pg_pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM daily_item_winners WHERE winner_date = $1
            )
            """,
            winner_date,
        )
        iggly_log(
            "db",
            f"Checked existence of daily winner for {winner_date}: {result}",
            bot=bot,
        )
        return result
