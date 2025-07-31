from typing import Any, Dict, Optional

from discord.ext import commands, tasks

from utils.set_promo_db import get_promo  # 🔍 Fetch promo data from DB


# ————————————————————————————————
# 🌸 Promo Cache – Holds current promo data for quick access
# ————————————————————————————————
class PromoCache:
    def __init__(self):
        self.promo: Optional[Dict[str, Any]] = None  # 📦 Cached promo or None

    # 🔄 Load promo data from DB into cache
    async def load_promo(self, bot):
        self.promo = await get_promo(bot)
        # ————————————————————————————————————————————————
        # 🌸 [DEBUG] Loaded promo data
        print(f"[💖 PROMO CACHE] Loaded promo: {self.promo}")
        # ————————————————————————————————————————————————

    # ✅ Check if promo is active in cache
    def is_promo_active(self) -> bool:
        # ————————————————————————————————————————————————
        # 🌸 [DEBUG] Checking if promo is active
        print(f"[💗 PROMO CACHE] Checking if promo is active: {self.promo is not None}")
        # ————————————————————————————————————————————————
        return self.promo is not None


promo_cache = PromoCache()  # 🏷️ Singleton cache instance


# 📦 Utility to get current cached promo (for other modules)
def get_active_promo_cache() -> Optional[Dict[str, Any]]:
    return promo_cache.promo


# ————————————————————————————————
# 🌸 Promo Refresher Cog – Periodically refreshes promo cache every 10 minutes
# ————————————————————————————————
class PromoRefresher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refresh_promo_cache.start()

    @tasks.loop(minutes=10)
    async def refresh_promo_cache(self):
        await promo_cache.load_promo(self.bot)

    @refresh_promo_cache.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()
        print("[💖 PROMO CACHE] Starting refresher loop...")

    @commands.Cog.listener()
    async def on_ready(self):
        # Force load promo cache once at startup
        await promo_cache.load_promo(self.bot)
        print("[💖 PROMO CACHE] Loaded promo cache at startup (on_ready)")


# ————————————————————————————————
# 🎀 Cog Setup – Adds PromoRefresher cog to the bot
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(PromoRefresher(bot))
