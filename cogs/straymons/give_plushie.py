from typing import Any, Dict
from zoneinfo import ZoneInfo

import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from cogs.straymons.promo_refresher import promo_cache  # 🎀 Import existing promo cache
from config.guild_ids import *
from config.straymons.constants import *
from config.straymons.emojis import Emojis
from utils.record_drop import record_manual_item_drop
from utils.visuals.clan_promo_embeds import build_give_plushie_embed

# 💗 Asia Manila timezone for any date/time operations
ASIA_MANILA = ZoneInfo("Asia/Manila")


class PlushieCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.plushie_methods = ["catch", "fish", "battle", "mew"]

    async def method_autocomplete(self, interaction: Interaction, current: str):
        current = current.lower()
        return [
            app_commands.Choice(name=method, value=method)
            for method in self.plushie_methods
            if current in method
        ][
            :25
        ]  # max 25 choices

    @app_commands.command(
        name="give-plushie", description="Manually give a plushie drop to a member"
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        member="The member to give the plushie to",
        method="Drop method",
        day="The day number of the drop",
    )
    @app_commands.autocomplete(method=method_autocomplete)
    async def give_plushie(
        self, interaction: Interaction, member: Member, method: str, day: int
    ):
        await interaction.response.defer(ephemeral=True)

        method = method.lower()
        if method not in self.plushie_methods:
            await interaction.followup.send(
                f"❌ Invalid method. Allowed: {', '.join(self.plushie_methods)}"
            )
            return

        promo = promo_cache.promo
        promo_emoji = promo["emoji"]
        promo_emoji_name = promo["emoji_name"]
        promo_name = promo["name"]

        await record_manual_item_drop(self.bot, member.id, method, day)

        hunt_channel = interaction.guild.get_channel(HUNT_CHANNEL_ID)
        if not hunt_channel:
            await interaction.followup.send("❌ Hunt channel not found.")
            return

        msg_link = f"[Manual Drop - Day {day}]"

        drop_track_embed = await build_give_plushie_embed(
            bot=self.bot,
            member=member,
            method=method,
            promo_emoji=promo_emoji,
            promo_emoji_name=promo_emoji_name,
            promo_name=promo_name,
            day=day,
        )

        await hunt_channel.send(embed=drop_track_embed)
        await interaction.followup.send(
            f"✅ Plushie drop given to {member.mention} by method `{method}` for day {day}."
        )


async def setup(bot):
    await bot.add_cog(PlushieCommands(bot))
