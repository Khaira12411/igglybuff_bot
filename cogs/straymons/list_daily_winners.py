from datetime import timedelta  # Added for date range calculation

import discord
from discord import app_commands
from discord.ext import commands

from config.straymons.constants import *
from config.straymons.emojis import Emojis
from utils.daily_winner_db import get_all_winners
from utils.misc.role_checks import *
from utils.visuals.random_pink import get_random_pink

divider_url = "https://media.discordapp.net/attachments/1393740397905313912/1399600790183608393/image.png?ex=6892290f&is=6890d78f&hm=7bdb56f9a2fb85a6f5844efe6c83cdfce7b207bd0cde9f7587cca946247920e2&=&format=webp&quality=lossless&width=1806&height=136"
thumbnail_url = "https://media.discordapp.net/attachments/1298966164072038450/1402129883785855046/8f6ba31c50d12f822589cf8a7147b8e6-removebg-preview.png?ex=6892cab6&is=68917936&hm=6b166addb71d6e7cff5e02a79727e5bd9ab52a9be588784b5b59a360f51dd123&=&format=webp&quality=lossless&width=596&height=530"


class DailyWinnersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=STRAYMONS_GUILD_ID))
    @app_commands.command(
        name="list-daily-winners",
        description="Show all daily winners ordered by day with drops",
    )
    @clan_staff_only()
    async def list_daily_winners(self, interaction: discord.Interaction):
        # 🌸✨ Defer response for dreamy embed build ✨🌸
        await interaction.response.defer()

        # 🎀 Fetch all winners from DB 🎀
        winners = await get_all_winners(self.bot)
        if not winners:
            return await interaction.followup.send(
                "No daily winners found.", ephemeral=True
            )

        # 🌷 Sort winners by winner_date ascending (day 1 first) 🌷
        winners.sort(key=lambda x: x["winner_date"])

        # 💖 Group winners by day for single field per day 💖
        winners_by_day = {}
        for win in winners:
            day = win["winner_date"]
            if day not in winners_by_day:
                winners_by_day[day] = []
            winners_by_day[day].append(win)

        # 💌 Prepare embed with pink vibes 💌
        embed = discord.Embed(
            # title=f"{Emojis.pink_party} Daily Winners Timeline",
            description=(
                f"## {Emojis.pink_party} Daily Winners Timeline\n"
                f"### Winners by day with total drops:\n"
            ),
            color=get_random_pink(),
        )
        embed.set_image(url=divider_url)
        embed.set_thumbnail(url=thumbnail_url)
        # 🩷 Add fields: one field per day with all winners that day 🩷
        day_number = 1
        for day, winners_list in winners_by_day.items():
            day_start = day
            day_end = day_start + timedelta(days=1)
            field_name = f"🌺 Day {day_number} | {day_start.strftime('%Y-%m-%d')} to {day_end.strftime('%Y-%m-%d')}"

            # If there's more than one winner, format with "Winners:" and list
            if len(winners_list) > 1:
                winners_lines = []
                total_drops = winners_list[0][
                    "total_drops"
                ]  # assume same drops for all ties

                for win in winners_list:
                    user_id = win["user_id"]
                    try:
                        member = interaction.guild.get_member(user_id)
                        display_name = member.display_name if member else None
                        if not display_name:
                            user = await self.bot.fetch_user(user_id)
                            display_name = user.name
                    except Exception:
                        display_name = f"User ID {user_id}"
                    winners_lines.append(f"> - - 🎀 {display_name}")

                field_value = (
                    "> - 🦄 Winners:\n"
                    + "\n".join(winners_lines)
                    + f"\n> - ✨ Total Drops: {total_drops} each"
                )
            else:
                # Only one winner: show normally
                win = winners_list[0]
                user_id = win["user_id"]
                total_drops = win["total_drops"]

                try:
                    member = interaction.guild.get_member(user_id)
                    display_name = member.display_name if member else None
                    if not display_name:
                        user = await self.bot.fetch_user(user_id)
                        display_name = user.name
                except Exception:
                    display_name = f"User ID {user_id}"

                field_value = (
                    f"> - 🦄 Winner: {display_name}\n"
                    f"> - ✨ Total Drops: {total_drops}"
                )

            embed.add_field(name=field_name, value=field_value, inline=False)
            day_number += 1

            if day_number > 25:  # Discord max fields safety check
                break

        # 🌸✨ Send embed to channel ✨🌸
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DailyWinnersCog(bot))
