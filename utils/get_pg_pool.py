import os
import ssl

import asyncpg


async def get_pg_pool():
    internal_url = os.getenv("DATABASE_URL")
    public_url = os.getenv("DATABASE_PUBLIC_URL")

    # 💖 Create SSL context that skips cert verification for snuggly secure vibes
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 🌸 Try internal URL with SSL verification disabled — fingers crossed! 🤞
    try:
        print(
            f"[🌸 DB INFO] Trying internal URL with SSL verification disabled: {internal_url}"
        )
        return await asyncpg.create_pool(dsn=internal_url, ssl=ssl_context)
    except Exception as e:
        print(f"[💔 DB WARN] Internal URL failed to connect:\n  → {e}")

    # 🧸 Fallback: Try public URL with SSL verification disabled — second chance sparkles ✨
    try:
        print(
            f"[🧸 DB INFO] Trying public URL with SSL verification disabled: {public_url}"
        )
        return await asyncpg.create_pool(dsn=public_url, ssl=ssl_context)
    except Exception as e:
        print(f"[💔 DB WARN] Public URL failed to connect:\n  → {e}")

    # 🌷 Oops! Both attempts failed — time for some troubleshooting hugs! 🤗
    raise ConnectionError(
        "💖 Could not connect to either internal or public Postgres database. Sending you cozy vibes to fix this! 💖"
    )
