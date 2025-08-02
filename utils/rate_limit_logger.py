import logging

# 🛡️ Your private log channel ID here
LOG_CHANNEL_ID = 1400998689018875904  # Bot Logs  # <-- change this

# 🧠 Known route-action mappings
ROUTE_LABELS = {
    "/users/@me": "fetch_self",
    "/users/": "fetch_user",  # ends with a user ID
    "/channels/": "send_or_fetch_message",
    "/messages/": "edit_or_delete_message",
    "/reactions": "add_or_clear_reaction",
    "/guilds/": "guild_fetch_or_edit",
    "/invites/": "invite_lookup",
    "/webhooks/": "webhook_action",
    "/stickers/": "sticker_update",
    "/roles/": "role_update",
}


class RateLimitLogger(logging.Handler):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def send_to_channel(self, message):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)

    def emit(self, record):
        message = record.getMessage()
        if "429" not in message and "rate limited" not in message.lower():
            return

        # Try to find route
        route_info = None
        label = None

        if "route" in message:
            parts = message.split("route")
            if len(parts) > 1:
                route_info = parts[-1].strip(" /")

                # Try to label the route
                for pattern, route_label in ROUTE_LABELS.items():
                    if pattern in route_info:
                        label = route_label
                        break

        # Build message
        log_msg = f"⚠️ **Rate limit warning!**\n```{message}```"
        if route_info:
            log_msg += f"\n🔗 Route: `{route_info}`"
        if label:
            log_msg += f"\n🔍 Likely action: **{label}**"

        try:
            self.bot.loop.create_task(self.send_to_channel(log_msg))
        except Exception:
            pass


def setup_rate_limit_logging(bot):
    logger = logging.getLogger("discord.http")

    # Prevent adding multiple handlers
    if any(isinstance(h, RateLimitLogger) for h in logger.handlers):
        return

    handler = RateLimitLogger(bot)
    handler.setLevel(logging.WARNING)  # Catch warnings and above only
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)

    # Set discord.http level to CRITICAL to suppress debug/info/warning logs
    logger.setLevel(logging.CRITICAL)
    logger.addHandler(handler)
