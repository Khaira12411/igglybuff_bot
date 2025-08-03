from datetime import datetime
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

        print("🩷 [SCHEDULER] Initializing scheduler and preparing job...")

        # 🌸 Schedule the sparkling daily announcement at noon Manila time
        self.scheduler.add_job(
            self.run_announcement,
            CronTrigger(hour=12, minute=0),
            id="daily_winner_announcement",
            replace_existing=True,
        )

        """# 🕑 Add a test tick job every minute to verify scheduler is running
        self.scheduler.add_job(
            self.test_tick,
            "interval",
            minutes=1,
            id="test_tick",
            replace_existing=True,
        )"""

        print("🌸 [SCHEDULER] Daily winner announcement job added! 🌼")
        print("🕑 [SCHEDULER] Test tick job added (prints every minute).")

        # 🩷 Start the scheduler so it can sprinkle daily joy
        self.scheduler.start()
        print("🩷 [SCHEDULER] Scheduler has started! Ready to sparkle ✨")

        # 🪷 Show scheduled job(s) now that they're initialized
        for job in self.scheduler.get_jobs():
            next_run = (
                job.next_run_time.isoformat()
                if job.next_run_time
                else "Not scheduled yet"
            )
            print(f"🔔 [SCHEDULER] Job ID: {job.id}, Next Run: {next_run}")

    """async def test_tick(self):
        now = datetime.now(ASIA_MANILA).strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"🕑 [SCHEDULER] Test tick fired at {now}")"""

    # 💗 The heart of the cog: run the announcement if we're still in the right guild
    async def run_announcement(self):
        now = datetime.now(ASIA_MANILA).strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"🕑 [SCHEDULER] run_announcement triggered at {now}")

        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            # 🌷 Oops! We're not in the guild anymore, skipping today’s shine
            print(
                f"💔 [SCHEDULER] Guild with ID {self.guild_id} not found. Skipping today’s twinkle!"
            )
            return

        # ✨ Yay! Announcing the daily winner for our lovely guild
        print(
            f"🎉 [SCHEDULER] Running daily winner announcement for {guild.name} ({guild.id}) 💝"
        )
        await announce_daily_winner(self.bot)


# 🎀 Cog setup: adding SchedulerCog with your special guild ID
async def setup(bot):
    await bot.add_cog(SchedulerCog(bot, STRAYMONS_GUILD_ID))
