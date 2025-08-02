from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from config.straymons.constants import STRAYMONS_GUILD_ID
from utils.announce_daily_winner import announce_daily_winner

ASIA_MANILA = ZoneInfo("Asia/Manila")


# 💖✨ SchedulerCog: Gently schedules our daily winner announcement ✨💖
class SchedulerCog(commands.Cog):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        # 🎀 Setting up the dreamy AsyncIOScheduler with Manila timezone magic
        self.scheduler = AsyncIOScheduler(timezone=ASIA_MANILA)

        # 🌸 Schedule the sparkling daily announcement at noon Manila time
        self.scheduler.add_job(
            self.run_announcement,
            CronTrigger(hour=12, minute=0),
            id="daily_winner_announcement",
            replace_existing=True,
        )
        # 🩷 Start the scheduler so it can sprinkle daily joy
        self.scheduler.start()

    # 💗 The heart of the cog: run the announcement if we're still in the right guild
    async def run_announcement(self):
        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            # 🌷 Oops! We're not in the guild anymore, skipping today’s shine
            print(
                f"[SchedulerCog] Guild with ID {self.guild_id} not found. Skipping announcement."
            )
            return

        # ✨ Yay! Announcing the daily winner for our lovely guild
        print(
            f"[SchedulerCog] Running daily winner announcement for guild {guild.name} ({guild.id})"
        )
        await announce_daily_winner(self.bot)


# 🎀 Cog setup: adding SchedulerCog with your special guild ID
async def setup(bot):
    # 💖 Replace 123456789012345678 with your actual guild ID 💖
    await bot.add_cog(SchedulerCog(bot, STRAYMONS_GUILD_ID))
