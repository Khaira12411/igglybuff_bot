import discord

from config.emojis import Emojis
from utils.visuals.random_pink import get_random_pink

bday_event_desc = f"""# {Emojis.sakura_moon} Skaia’s Birthday Event
-# From today until <t:1754971200:f>, a promo event will commence. There is a chance at getting a Mew plushie drop from `;pokemon`, `;fish` and `;battle`.

Every day at reset, the member with the highest plushies on that day will be rewarded an Alolan-Vulpix. Each winner can only claim **two** Alolan-Vulpix for the duration of the event. The plushies __will not__ reset after receiving the daily reward. This will continue until the last day, where the there highest winners will be rewarded with:

{Emojis.num_1} {Emojis.golden} Gardevoir + 10M {Emojis.pokecoin}
{Emojis.num_2} {Emojis.golden} Diancie + 5M {Emojis.pokecoin}
{Emojis.num_3} {Emojis.golden} Keldeo + 2.5M {Emojis.pokecoin}
-# Each participating members with <@&1311408569945686138> will also get 1M {Emojis.pokecoin} as participation rewards."""


def build_birthday_event_embed():
    embed = discord.Embed(description=bday_event_desc, color=get_random_pink())
    return embed


def build_drop_track_embed(
    member: discord.Member,
    method: str,
    promo_emoji: str,
    promo_emoji_name: str,
    promo_name: str,
):
    if method == "catch":
        bullet_emoji = Emojis.pink_flower
        method_emoji = Emojis.pink_ball
        method_name = "Catching"
        color = 16745343
        footer_emoji = "🌸"

    if method == "fish":
        bullet_emoji = Emojis.pink_bow
        method_emoji = Emojis.pink_fish_rod
        color = 16752762
        method_name = "Fishing"
        footer_emoji = "💗"

    if method == "battle":
        bullet_emoji = Emojis.pink_heart2
        method_emoji = Emojis.pink_swords
        color = 14315798
        method_name = "Battling"
        footer_emoji = "🩰"

    embed = discord.Embed(
        description=f"{bullet_emoji} {member.mention} has found a {promo_emoji} **{promo_emoji_name}** from {method_emoji} {method_name} for {promo_name}!",
        color=color,
    )
    # embed.set_footer(text=f"{footer_emoji} {promo_name}")
    return embed


