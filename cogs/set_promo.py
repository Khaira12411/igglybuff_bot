from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config.constants import *
from config.emojis import Emojis
from utils.set_promo_db import set_promo_data
from utils.visuals.clan_promo_embeds import build_birthday_event_embed
from utils.visuals.random_pink import get_random_pink

end_ts = "<t:1754971200:f>"
# ————————————————————————————————
# 🛡️ Staff Role Check – Only trusted hands allowed!
# ————————————————————————————————
STAFF_ROLE_IDS = {STAFF_ROLE_ID, 987654321098765432}  # replace with your real IDs


def parse_rate(rate_str: str) -> Optional[int]:
    """🎯 Convert '1/250' or '250' to just 250 for cleaner data."""
    try:
        if "/" in rate_str:
            parts = rate_str.split("/")
            if len(parts) == 2 and parts[0].strip() == "1":
                return int(parts[1].strip())
        return int(rate_str)
    except ValueError:
        return None


class PromoManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff():
        def predicate(interaction: discord.Interaction) -> bool:
            return any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles)

        return app_commands.check(predicate)

    # ————————————————————————————————
    # 🌟 Promo Setup Command – Make your magic drop sparkle!
    # ————————————————————————————————
    @app_commands.command(
        name="set-promo",
        description="🌸 Set or update a special promo event with drop rates and roles!",
    )
    @is_staff()
    @app_commands.describe(
        name="Name of the promo event",
        emoji="Emoji shown in drops and embeds",
        emoji_name="Emoji name to store in database (no colons!)",
        prize="Prize for this promo",
        image_url="Image URL for the promo embed",
        catch_rate="Catch drop rate (e.g. 250 or 1/250)",
        battle_rate="Battle drop rate",
        fish_rate="Fish drop rate",
        whitelist_role="Role allowed to get drops",
        number_before_claim="Optional number before claiming (default 0)",
    )
    async def set_promo(
        self,
        interaction: discord.Interaction,
        name: str,
        emoji: str,
        emoji_name: str,
        prize: str,
        image_url: str,
        catch_rate: str,
        battle_rate: str,
        fish_rate: str,
        whitelist_role: Optional[discord.Role] = None,
        number_before_claim: Optional[int] = 0,
    ):
        # ————————————————————————————————
        # 🔍 Validate and parse drop rates
        # ————————————————————————————————
        catch = parse_rate(catch_rate)
        battle = parse_rate(battle_rate)
        fish = parse_rate(fish_rate)

        if not all([catch, battle, fish]) or catch < 1 or battle < 1 or fish < 1:
            await interaction.response.send_message(
                "⚠️ Invalid drop rate(s). Please use a number like `250` or `1/250`.",
                ephemeral=True,
            )
            return

        # ————————————————————————————————
        # 💾 Save to database
        # ————————————————————————————————
        await set_promo_data(  # """
            bot=self.bot,
            name=name,
            emoji=emoji,
            emoji_name=emoji_name,
            prize=prize,
            image_url=image_url,
            catch_rate=catch,
            battle_rate=battle,
            fish_rate=fish,
            whitelist_role_id=whitelist_role.id if whitelist_role else None,
            number_before_claim=number_before_claim,
        )  # """

        # ————————————————————————————————
        # ✨ Confirmation Embed – It's official!
        # ————————————————————————————————
        desc = f""" # {Emojis.pink_star} {name}

{Emojis.pink_bow} Members can obtain {emoji} **{emoji_name}** from:
- {Emojis.pink_ball} Catching Pokemon `/pokemon` ({catch_rate})
- {Emojis.pink_fish_rod} Fishing `/fish` ({fish_rate})
- {Emojis.pink_swords} Battling NPCs `/battle` ({battle_rate})

{Emojis.pink_exclamation} Notes:
- {emoji} can only drop in this server!
- Members must have <@&{HERSHEY_ROLE_ID}>, and <@&{DONATED_ROLE_ID}> to be eligible for {emoji} drops!
- Use `/clan-promo-view` to check your progress

{Emojis.pink_calendar} **Available until: {end_ts}**"""
        embed = discord.Embed(
            title=f"{emoji} Promo '{name}' has been set!",
            description=desc,
            color=get_random_pink(),
        )
        embed.set_image(url=image_url)

        await interaction.response.send_message(embed=embed)
        events_news_channel = interaction.guild.get_channel(EVENT_NEWS_ID)

        embed = discord.Embed(
            description=desc,
            color=get_random_pink(),
        )
        content = f"<@&{STRAYMONS_ROLE_ID}> {name} is live!"
        embed.set_image(url=image_url)
        bday_embed = build_birthday_event_embed()
        await events_news_channel.send(content=content, embeds=[bday_embed, embed])


# ————————————————————————————————
# 🔧 Cog Setup – Load the magic into the bot!
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(PromoManager(bot))
