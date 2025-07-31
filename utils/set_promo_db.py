from typing import Any, Dict, Optional


# ————————————————————————————————
# 🔍 Promo Checkers – Retrieve promo data or existence
# ————————————————————————————————
async def promo_exists(bot) -> Optional[Dict[str, Any]]:
    """🌸 Return promo dict if a promo exists, else None. Assumes one promo at a time."""
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM clan_promo_events LIMIT 1")
        if row:
            return dict(row)
        return None


async def get_promo(bot) -> Optional[Dict[str, Any]]:
    """🌸 Return the active promo dict or None."""
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM clan_promo_events LIMIT 1")
        if row:
            return dict(row)
        return None


# ————————————————————————————————
# 💾 Promo Insert/Update – Save or overwrite promo data by name
# ————————————————————————————————
async def save_promo(
    bot,
    name: str,
    emoji: str,
    prize: str,
    image_url: str,
    catch_rate: int,
    battle_rate: int,
    fish_rate: int,
    whitelist_role_id: Optional[int] = None,
    number_before_claim: int = 0,
):
    """🌸 Insert or update promo by name."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO clan_promo_events
            (name, emoji, prize, image_url, catch_rate, battle_rate, fish_rate, whitelist_role_id, number_before_claim)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (name) DO UPDATE SET
              emoji = EXCLUDED.emoji,
              prize = EXCLUDED.prize,
              image_url = EXCLUDED.image_url,
              catch_rate = EXCLUDED.catch_rate,
              battle_rate = EXCLUDED.battle_rate,
              fish_rate = EXCLUDED.fish_rate,
              whitelist_role_id = EXCLUDED.whitelist_role_id,
              number_before_claim = EXCLUDED.number_before_claim,
              updated_at = NOW()
            """,
            name,
            emoji,
            prize,
            image_url,
            catch_rate,
            battle_rate,
            fish_rate,
            whitelist_role_id,
            number_before_claim,
        )


# ————————————————————————————————
# 🗑️ Promo Delete – Remove promo by name
# ————————————————————————————————
async def delete_promo(bot, name: str):
    """🌸 Delete promo by name."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute("DELETE FROM clan_promo_events WHERE name = $1", name)


# ————————————————————————————————
# ✨ Promo Partial Update – Update only specified fields (non-None) for a promo
# ————————————————————————————————
async def update_promo(
    bot,
    name: str,
    emoji: Optional[str] = None,
    prize: Optional[str] = None,
    image_url: Optional[str] = None,
    catch_rate: Optional[int] = None,
    battle_rate: Optional[int] = None,
    fish_rate: Optional[int] = None,
    whitelist_role_id: Optional[int] = None,
    number_before_claim: Optional[int] = None,
):
    """🌸 Update specified fields of a promo by name. Only non-None params are updated."""
    if all(
        v is None
        for v in [
            emoji,
            prize,
            image_url,
            catch_rate,
            battle_rate,
            fish_rate,
            whitelist_role_id,
            number_before_claim,
        ]
    ):
        return  # Nothing to update

    set_clauses = []
    values = []
    idx = 1

    def add_set(field, val):
        nonlocal idx
        set_clauses.append(f"{field} = ${idx}")
        values.append(val)
        idx += 1

    if emoji is not None:
        add_set("emoji", emoji)
    if prize is not None:
        add_set("prize", prize)
    if image_url is not None:
        add_set("image_url", image_url)
    if catch_rate is not None:
        add_set("catch_rate", catch_rate)
    if battle_rate is not None:
        add_set("battle_rate", battle_rate)
    if fish_rate is not None:
        add_set("fish_rate", fish_rate)
    if whitelist_role_id is not None:
        add_set("whitelist_role_id", whitelist_role_id)
    if number_before_claim is not None:
        add_set("number_before_claim", number_before_claim)

    # Always update updated_at timestamp
    set_clauses.append("updated_at = NOW()")

    async with bot.pg_pool.acquire() as conn:
        query = f"""
        UPDATE clan_promo_events SET
            {', '.join(set_clauses)}
        WHERE name = ${idx}
        """
        values.append(name)
        await conn.execute(query, *values)


async def set_promo_data(
    bot,
    name,
    emoji,
    prize,
    image_url,
    catch_rate,
    battle_rate,
    fish_rate,
    whitelist_role_id,
    number_before_claim,
    emoji_name,
):
    pool = bot.pg_pool
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO clan_promo_events (
                name, emoji, prize, image_url, catch_rate, battle_rate, fish_rate, whitelist_role_id, number_before_claim, emoji_name
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9, $10)
            ON CONFLICT (name)
            DO UPDATE SET
                emoji = EXCLUDED.emoji,
                prize = EXCLUDED.prize,
                image_url = EXCLUDED.image_url,
                catch_rate = EXCLUDED.catch_rate,
                battle_rate = EXCLUDED.battle_rate,
                fish_rate = EXCLUDED.fish_rate,
                whitelist_role_id = EXCLUDED.whitelist_role_id,
                number_before_claim = EXCLUDED.number_before_claim,
                emoji_name = EXCLUDED.emoji_name;
            """,
            name,
            emoji,
            prize,
            image_url,
            catch_rate,
            battle_rate,
            fish_rate,
            whitelist_role_id,
            number_before_claim,
            emoji_name,
        )
