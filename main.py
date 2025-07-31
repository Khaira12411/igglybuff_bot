import logging

# Suppress discord.py logs (must be set BEFORE imports)
logging.basicConfig(level=logging.WARNING)
for logger_name in [
    "discord",
    "discord.client",
    "discord.gateway",
    "discord.http",
    "discord.voice_client",
    "asyncio",
]:
    # Suppress the PyNaCl voice support warning
    logging.getLogger("discord.client").setLevel(logging.ERROR)
    logging.getLogger(logger_name).setLevel(logging.WARNING)

import glob
import os
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from cogs.promo_refresher import get_active_promo_cache, promo_cache
from utils.get_pg_pool import get_pg_pool
from utils.set_promo_db import get_promo

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ASIA_MANILA = ZoneInfo("Asia/Manila")

MORNING_STATUSES = [
    (discord.ActivityType.playing, "good morning, Straymons! 🌸"),
    (discord.ActivityType.listening, "to morning berry tea being sipped 🧃"),
    (discord.ActivityType.watching, "the sunrise while gathering plushies ☀️"),
]

NIGHT_STATUSES = [
    (discord.ActivityType.playing, "dreaming of rare plushies 🌙"),
    (discord.ActivityType.listening, "to lullabies in a flower bed 💤"),
    (discord.ActivityType.watching, "starlight sorting clan drops 🧺"),
]

PROMO_THEMES = [
    (discord.ActivityType.playing, "the promo hunt is live! 🎀"),
    (discord.ActivityType.listening, "to jingles while earning promo points 💖"),
    (discord.ActivityType.watching, "plushies being collected 🧸"),
]

DEFAULT_STATUSES = [
    (discord.ActivityType.playing, "gently glowing, still shining 🌸"),
    (discord.ActivityType.listening, "to tiny tunes humming softly 💗"),
    (discord.ActivityType.watching, "petals dance in the breeze 🌷"),
    (discord.ActivityType.playing, "floating gently on soft sparkles 🍓"),
    (discord.ActivityType.listening, "to dreams cuddled in code 🧸"),
    (discord.ActivityType.watching, "bedtime stories unfolding 🩷"),
]


def get_time_based_statuses():
    now = datetime.now(ASIA_MANILA)
    return MORNING_STATUSES if 6 <= now.hour < 18 else NIGHT_STATUSES


# 💗 Load promo into cache manually at startup (so it's ready before any commands use it)
async def preload_promo(bot):
    promo_cache.promo = await get_promo(bot)
    print("[💖 PROMO CACHE] Loaded promo cache at startup (on_ready)")


async def get_dynamic_status_tuple():
    promo = get_active_promo_cache()
    if promo:
        return random.choice(PROMO_THEMES)
    else:
        return random.choice(get_time_based_statuses() + DEFAULT_STATUSES)


@tasks.loop(minutes=5)
async def status_rotator():
    activity_type, message = await get_dynamic_status_tuple()
    print(f"[💖 STATUS] Switching to: {activity_type.name} → {message}")
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


# ——————————————————————————————————————————————
# 🌸 on_ready Event – Sync Slash Commands at Startup
# ——————————————————————————————————————————————
@bot.event
async def on_ready():
    print(
        f"[💗✨ IGGLYBUFF] I’m awake and twinkling as {bot.user} ✨ Ready to sparkle!\n"
    )

    # 💗 Load promo early so presence/status + commands have access to it
    await preload_promo(bot)

    # 🌷 Ensure all application (slash) commands are registered with Discord
    await bot.tree.sync()
    print("[🌷 Commands] Slash commands synced with Discord successfully! 💫")

    # 💖 Confirm PostgreSQL connection
    if hasattr(bot, "pg_pool"):
        print("[🌸 Database] PostgreSQL connection pool is ready! 🧺")
    else:
        print("[⚠️ Warning] pg_pool is not attached!")

    # 💤 Start the rotating presence/status loop
    if not status_rotator.is_running():
        print("[🩷 STATUS] Starting Igglybuff’s dreamy thoughts loop... 🌙")
        status_rotator.start()

    # ✨ Set a soft, rotating presence
    activity_type, message = await get_dynamic_status_tuple()
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


@bot.event
async def setup_hook():
    print("[💘 SETUP] Snuggling up the database and gathering dreams...")

    try:
        pg_pool = await get_pg_pool()
        async with pg_pool.acquire() as conn:
            version = await conn.fetchval("SELECT version();")
            print(f"[🧺 Postgres] Connected! Version: {version}")
        bot.pg_pool = pg_pool
    except Exception as e:
        print(f"[❌ Postgres] Connection failed: {e}")

    loaded_count = 0
    for cog_path in glob.glob("cogs/*.py"):
        filename = os.path.basename(cog_path)
        module_name = filename[:-3].replace("-", "_")
        cog_name = f"cogs.{module_name}"
        try:
            await bot.load_extension(cog_name)
            loaded_count += 1
        except Exception as e:
            print(f"[💔 COG] Failed to load {cog_name}: {e}")

    print(f"[🎀 COGS] All fluffed up: {loaded_count} cogs loaded successfully! 🌸")


if __name__ == "__main__":
    load_dotenv()
    print("[💗💫 IGGLYBUFF] Waking up softly... fluffing hair...")

    while True:
        try:
            bot.run(os.getenv("DISCORD_TOKEN"))
        except Exception as e:
            print(f"[⚠️ ERROR] Bot crashed with error: {e}")
            print("♻️ Restarting Igglybuff in 5 seconds...")
            time.sleep(5)
