# 🩷 utils/iggly_log_helpers.py

import traceback
from enum import Enum

import discord
from discord.ext import commands


# 🩰 Iggly server context
class IgglyContext(Enum):
    IGLY = "iggly"
    STRAYMONS = "straymons"  # 👈 add others if needed!


# 🍥 Pink tags for Iggly's dreamy logs
IGGLY_TAGS = {
    "db": "🩷 DB INFO",
    "cmd": "🌸 COMMAND",
    "ready": "🎀 READY",
    "error": "💢 ERROR",
    "skip": "🍼 SKIP",
    "sent": "🍬 SENT",
    "warn": "🩹 WARN",
    "critical": "💔 CRITICAL",
    "schedule_success": "✅ SCHEDULE",  # 🆕 Scheduler success logs
}

# 💌 Optional: set this if Iggly should send critical messages to a channel
IGGLY_CRITICAL_CHANNEL_ID = 1400998689018875904


def iggly_log(
    tag: str,
    message: str,
    *,
    label: str = None,  # Optional sub-label (e.g. error ID)
    source: str = None,  # Optional cog/module/cmd name (e.g. SchedulerCog)
    bot: commands.Bot = None,
    include_trace: bool = False,
    context=None,  # Optional IgglyContext
):
    prefix = IGGLY_TAGS.get(tag, "🌷 NOTE")

    # Compose [prefix : source] or [prefix] fallback
    if source:
        header = f"[{prefix} : {source}]"
    else:
        header = f"[{prefix}]"

    # Optional context display as a label
    context_str = f"[{context.name.upper()}]" if context else ""

    # Optional custom label
    label_str = f"[{label}]" if label else ""

    # Combine everything
    log_message = f"{header} {context_str}{label_str} {message}".strip()
    print(log_message)

    # 💔 Send critical errors to Discord channel
    if tag == "critical" and bot:
        try:
            channel = bot.get_channel(IGGLY_CRITICAL_CHANNEL_ID)
            if channel:
                full_message = f"`{prefix}` {context_str}{label_str} {message}"
                if include_trace:
                    full_message += f"\n```py\n{traceback.format_exc()}```"
                if len(full_message) > 2000:
                    full_message = full_message[:1997] + "..."
                bot.loop.create_task(channel.send(full_message))
        except Exception:
            print("[💢 ERROR] Failed to send critical log to Discord:")
            traceback.print_exc()
            traceback.print_exc()
