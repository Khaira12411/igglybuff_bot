from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from config.straymons.constants import STRAYMONS_GUILD_ID
from utils.announce_daily_winner import announce_daily_winner
from utils.visuals.iggly_log_helpers import IgglyContext, iggly_log

ASIA_MANILA = ZoneInfo("Asia/Manila")


# 💖✨ SchedulerCog: Gently schedules our daily winner announcement ✨💖
class SchedulerCog(commands.Cog):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.context = IgglyContext.IGLY

        # 🎀 Setting up the dreamy AsyncIOScheduler with Manila timezone magic
        self.scheduler = AsyncIOScheduler(timezone=ASIA_MANILA)

        self.log("ready", "Initializing scheduler and preparing job...")

        # 🌸 Schedule the sparkling daily announcement at noon Manila time
        self.scheduler.add_job(
            self.run_announcement,
            CronTrigger(hour=12, minute=0, timezone=ASIA_MANILA),
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

        self.log("ready", "Daily winner announcement job added! 🌼")
        self.log("ready", "Test tick job added (prints every minute).")

        # 🩷 Start the scheduler so it can sprinkle daily joy
        self.scheduler.start()
        self.log("ready", "Scheduler has started! Ready to sparkle ✨")

        # 🪷 Show scheduled job(s) now that they're initialized
        for job in self.scheduler.get_jobs():
            raw_next_run = job.next_run_time

            if raw_next_run:
                if raw_next_run.tzinfo is None:
                    # Naive datetime — assume UTC and convert
                    from datetime import timezone

                    aware_next_run = raw_next_run.replace(
                        tzinfo=timezone.utc
                    ).astimezone(ASIA_MANILA)
                else:
                    # Already timezone-aware — convert to Manila
                    aware_next_run = raw_next_run.astimezone(ASIA_MANILA)
                next_run_str = job.next_run_time.strftime("%Y-%m-%d %I:%M:%S %p")
            else:
                next_run_str = "Not scheduled yet"
            self.log("info", f"Job ID: {job.id}, Next Run (Manila): {next_run_str}")

    def log(self, tag: str, message: str, **kwargs):
        """Helper to log with source as this cog's class name, without context."""
        iggly_log(
            tag,
            message,
            # Remove context param here to skip printing [IGLY]
            source=self.__class__.__name__,
            **kwargs,
        )

    """async def test_tick(self):
        now = datetime.now(ASIA_MANILA).strftime("%Y-%m-%d %H:%M:%S %Z")
        self.log("info", f"Test tick fired at {now}")"""

    # 💗 The heart of the cog: run the announcement if we're still in the right guild
    async def run_announcement(self):
        now_str = datetime.now(ASIA_MANILA).strftime("%Y-%m-%d %I:%M:%S %p %Z")
        self.log("info", f"run_announcement triggered at {now_str}")

        try:
            guild = self.bot.get_guild(self.guild_id)
            if guild is None:
                # 🌷 Oops! We're not in the guild anymore, skipping today’s shine
                self.log(
                    "critical",
                    f"Guild with ID {self.guild_id} not found. Skipping today’s twinkle!",
                    bot=self.bot,
                )
                return

            # ✨ Yay! Announcing the daily winner for our lovely guild
            self.log(
                "ready",
                f"Running daily winner announcement for {guild.name} ({guild.id}) 💝",
            )
            await announce_daily_winner(self.bot)
            # 🎀 Job finished successfully — log success here
            self.log(
                "schedule_success",
                "Daily winner announcement ran smoothly.",
                bot=self.bot,
            )

        except Exception as e:
            self.log(
                "critical",
                f"Exception in run_announcement: {e}",
                bot=self.bot,
                include_trace=True,
            )


# 🎀 Cog setup: adding SchedulerCog with your special guild ID
async def setup(bot):
    await bot.add_cog(SchedulerCog(bot, STRAYMONS_GUILD_ID))
