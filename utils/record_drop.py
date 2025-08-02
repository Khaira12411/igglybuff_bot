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
        # 🔍 Get the current day from the DB
        row = await conn.fetchrow("SELECT day_number FROM current_day LIMIT 1;")
        current_day = row["day_number"] if row else 1  # fallback default

        # 📥 Record the drop with day label
        await conn.execute(
            """
            INSERT INTO member_item_drops (user_id, method, drop_time, day)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            method,
            drop_time,
            current_day,
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


# 💕 Get number of item drops for today (based on current day label)
async def get_daily_drops(bot, user_id: int) -> int:
    async with bot.pg_pool.acquire() as conn:
        # 🌸 Get current day from current_day table
        current_day = await conn.fetchval("SELECT day_number FROM current_day LIMIT 1")

        if current_day is None:
            print("[WARN] current_day table has no value.")
            return 0

        # 🍃 Count how many drops the user has on the current day
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM member_item_drops
            WHERE user_id = $1 AND day = $2
            """,
            user_id,
            current_day,
        )
        return result or 0
