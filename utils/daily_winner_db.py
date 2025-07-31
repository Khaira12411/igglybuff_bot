from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import discord

# 💖 Asia Manila timezone for all date/time operations
ASIA_MANILA = ZoneInfo("Asia/Manila")


# ————————————————————————————————
# 💖 Daily Winner Management – Insert or update the daily winner record
# ————————————————————————————————
async def set_daily_winner(
    bot,
    user_id: int,
    total_drops: int,
    winner_date: Optional[date] = None,
):
    """💖 Insert or update the daily winner for a given date (default: today)."""
    if winner_date is None:
        winner_date = date.today()

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO daily_item_winners (winner_date, user_id, total_drops)
            VALUES ($1, $2, $3)
            ON CONFLICT (winner_date) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                total_drops = EXCLUDED.total_drops,
                recorded_at = NOW()
            """,
            winner_date,
            user_id,
            total_drops,
        )


# ————————————————————————————————
# 💖 Retrieve daily winner info for a specific date (default: today)
# ————————————————————————————————
async def get_daily_winner(bot, winner_date: Optional[date] = None) -> Optional[Dict]:
    """💖 Get the winner row for a specific date, returns dict or None."""
    if winner_date is None:
        winner_date = date.today()

    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_item_winners WHERE winner_date = $1",
            winner_date,
        )
        return dict(row) if row else None


# ————————————————————————————————
# 💖 Fetch all daily winners ordered by most recent first
# ————————————————————————————————
async def get_all_winners(bot) -> List[Dict]:
    """💖 Get all daily winners ordered by winner_date DESC."""
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM daily_item_winners ORDER BY winner_date DESC"
        )
        return [dict(row) for row in rows]


# ————————————————————————————————
# 💖 Clear all daily winner records from the table
# ————————————————————————————————
async def clear_daily_winners(bot):
    """💖 Delete all rows from the daily_item_winners table."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute("DELETE FROM daily_item_winners")


# ————————————————————————————————
# 💖 Get top daily drops for a specific day in Asia/Manila timezone
# ————————————————————————————————
async def get_top_daily_drops(bot, day: datetime) -> List[Tuple[int, int]]:
    """
    💖 Retrieve (user_id, drops_count) for a given day.
    day: datetime (date portion used, timezone Asia/Manila)
    """
    day = day.astimezone(ASIA_MANILA)
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, COUNT(*) AS drops_count
            FROM member_item_drops
            WHERE drop_time >= $1 AND drop_time < $2
            GROUP BY user_id
            ORDER BY drops_count DESC;
            """,
            day_start,
            day_end,
        )
        return [(r["user_id"], r["drops_count"]) for r in rows]


# ————————————————————————————————
# 💖 Get top 3 users with most drops over the last `days` days
# ————————————————————————————————
async def get_top_drops_in_range(bot, days: int = 12) -> List[Tuple[int, int]]:
    """
    💖 Retrieve top 3 (user_id, total_drops) over the past `days` days.
    Uses Asia/Manila timezone.
    """
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
        return [(r["user_id"], r["total_drops"]) for r in rows]


async def get_daily_winner_count(bot: discord.Client, user_id: int) -> int:
    query = "SELECT COUNT(*) FROM daily_item_winners WHERE user_id = $1"
    async with bot.pg_pool.acquire() as conn:
        count = await conn.fetchval(query, user_id)
    return count or 0
