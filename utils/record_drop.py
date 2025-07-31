from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ASIA_MANILA = ZoneInfo("Asia/Manila")


async def record_item_drop(
    bot,
    user_id: int,
    method: str,
    drop_time: datetime = None,
):
    drop_time = drop_time or datetime.now(tz=ASIA_MANILA)
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO member_item_drops (user_id, method, drop_time)
            VALUES ($1, $2, $3)
            """,
            user_id,
            method,
            drop_time,
        )


# 💖 Get total number of item drops for a user
async def get_total_drops(bot, user_id: int) -> int:
    async with bot.pg_pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM member_item_drops
            WHERE user_id = $1
            """,
            user_id,
        )
        return result or 0


# 💕 Get number of item drops for today (12PM–12PM window)
async def get_daily_drops(bot, user_id: int) -> int:
    now = datetime.now(tz=ASIA_MANILA)

    # 🌸 Find the most recent 12 PM anchor
    if now.hour < 12:
        # It's before 12PM, so start from yesterday 12PM
        start_time = now.replace(
            hour=12, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
    else:
        # It's after 12PM, start from today 12PM
        start_time = now.replace(hour=12, minute=0, second=0, microsecond=0)

    # 🌷 End time is exactly 24 hours after
    end_time = start_time + timedelta(days=1)

    async with bot.pg_pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM member_item_drops
            WHERE user_id = $1 AND drop_time >= $2 AND drop_time < $3
            """,
            user_id,
            start_time,
            end_time,
        )
        return result or 0
