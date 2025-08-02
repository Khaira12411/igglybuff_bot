# ———————————————————————————————————————————————
# 🌸 /clan-promo-view — Show current promo + drop stats
# ———————————————————————————————————————————————

from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

from cogs.straymons.promo_refresher import get_active_promo_cache
from config.guild_ids import STRAYMONS_GUILD_ID
from config.straymons.constants import *
from config.straymons.emojis import Emojis
from utils.record_drop import get_daily_drops, get_total_drops
from utils.visuals.random_pink import get_random_pink

ASIA_MANILA = ZoneInfo("Asia/Manila")
end_ts = "<t:1754971200:f>"


class ClanPromo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="clan-promo-view",
        description="🌸 View current clan promo and your plushie progress!",
    )
    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    async def clan_promo_view(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        user = interaction.user

        # 🌸 Get current active promo
        promo_data = get_active_promo_cache()
        print(f"[DEBUG] Promo data from cache: {promo_data}")

        if not promo_data:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="🌸 No Ongoing Promo",
                    description="There's currently no active clan promo!",
                    color=discord.Color.pink(),
                )
            )

        # 📝 Promo info
        title = promo_data["name"]
        image_url = promo_data["image_url"]
        emoji = promo_data["emoji"]
        emoji_name = promo_data["emoji_name"]
        catch_rate = promo_data["catch_rate"]
        fish_rate = promo_data["fish_rate"]
        battle_rate = promo_data["battle_rate"]
        prize = promo_data["prize"]

        # 🧸 Drop stats
        total_drops = await get_total_drops(self.bot, user.id)
        today_drops = await get_daily_drops(self.bot, user.id)
        desc = f"""# {Emojis.pink_moon} {title}
## {Emojis.pink_gift} Daily Prize: {prize}

{Emojis.pink_bow} {emoji} **{emoji_name}** Drop Rates:
- {Emojis.pink_ball} Catching Pokemon `/pokemon` (1/{catch_rate})
- {Emojis.pink_fish_rod} Fishing `/fish` (1/{fish_rate})
- {Emojis.pink_swords} Battling NPCs `/battle` (1/{battle_rate})

{Emojis.pink_exclamation} Notes:
- {emoji} can only drop in this server!
- Members must have <@&{HERSHEY_ROLE_ID}>, and <@&{DONATED_ROLE_ID}> to be eligible for {emoji} drops!

{Emojis.pink_paper} Your Plushie Drops:
- {Emojis.pink_bear} Total Plushie Drops: {total_drops}
- {Emojis.pink_cake} Today's Drops: {today_drops}

{Emojis.pink_calendar} **Available until: {end_ts}**"""
        embed = discord.Embed(
            description=desc,
            color=get_random_pink(),
        )
        embed.set_footer(text="🌺 Promo stats reset daily at 12:00 PM (Asia/Manila)")
        embed.set_image(url=image_url)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ClanPromo(bot))
