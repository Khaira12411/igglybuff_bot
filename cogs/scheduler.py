from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from utils.announce_daily_winner import *

ASIA_MANILA = ZoneInfo("Asia/Manila")


class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=ASIA_MANILA)
        self.scheduler.add_job(
            self.run_announcement,
            CronTrigger(hour=12, minute=0),
            id="daily_winner_announcement",
            replace_existing=True,
        )
        self.scheduler.start()

    async def run_announcement(self):
        await announce_daily_winner(self.bot)


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
