import random
import re
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from cogs.promo_refresher import promo_cache  # 🎀 Import existing promo cache
from config.constants import *
from config.emojis import Emojis
from utils.record_drop import record_item_drop
from utils.set_promo_db import get_promo
from utils.visuals.clan_promo_embeds import build_drop_track_embed

# 💗 Asia Manila timezone for any date/time operations
ASIA_MANILA = ZoneInfo("Asia/Manila")


# ————————————————————————————————
# 🎀 EventWatcher Cog – Listens for PokéMeow messages & handles plushie drops
# ————————————————————————————————
class EventWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelisted_members = set()  # 🧂 Your whitelist cache

    # 💌 Handle new messages, only from PokéMeow bot
    async def handle_new_message(self, message: discord.Message):

        if message.author.id != POKEMEOW_ID:
            return

        if not promo_cache.is_promo_active():
            print("💤 [SKIP] No active promo, skipping plushie drop check.")
            return

        promo = promo_cache.promo
        await self.process_npc_drops(message, promo)

    # 💌 Handle edited messages for hershey drops
    async def handle_edit_message(self, message: discord.Message):
        if message.author.id != POKEMEOW_ID:
            return

        if not promo_cache.is_promo_active():
            return

        promo = promo_cache.promo
        await self.process_hershey_drops(message, promo)

    # 🎯 Process battle messages to possibly award NPC plushie drops
    async def process_npc_drops(self, message: discord.Message, promo: Dict[str, Any]):
        content = message.content.lower()
        if (
            "won the battle" in content
            and "you received" in content
            and "pokecoin" in content
        ):
            username_match = re.search(r"\*\*(.+?)\*\*", message.content)
            if not username_match:
                print("⚠️ [WARN] Username not found in battle message.")
                return

            username = username_match.group(1)
            member = discord.utils.find(
                lambda m: m.name == username or m.display_name == username,
                message.guild.members,
            )
            if not member:
                print(f"⚠️ [WARN] Member '{username}' not found in guild.")
                return

            if member.id not in self.whitelisted_members:
                return

            promo_emoji = promo["emoji"]
            promo_name = promo["name"]
            promo_emoji_name = promo["emoji_name"]
            drop_type = "npc"
            roll = random.randint(1, promo["battle_rate"])
            rate = promo["battle_rate"]
            # print(f"🎲 [ROLL] {member.display_name} rolled {roll} (1 out of {rate})")

            if roll == 1:
                drop_msg = f"{member.mention} has discovered a **{promo_emoji_name}** {promo_emoji} from battle! {Emojis.pink_heart_movin}"
                print(f"🎉 {drop_msg}")
                drop_message = await message.channel.send(drop_msg)
                drop_message_id = drop_message.id
                msg_link = f"[{Emojis.pink_link} Message Link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{drop_message_id})"
                await record_item_drop(self.bot, member.id, drop_type)
                hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

                drop_track_embed = build_drop_track_embed(
                    bot=self.bot,
                    member=member,
                    method="battle",
                    promo_emoji=promo_emoji,
                    promo_emoji_name=promo_emoji_name,
                    promo_name=promo_name,
                    msg_link=msg_link,
                )
                await hunt_channel.send(embed=drop_track_embed)

    # 🎯 Process hershey reply messages to check for fish or catch plushie drops
    async def process_hershey_drops(
        self, message: discord.Message, promo: Dict[str, Any]
    ):
        if not message.guild or not message.reference:
            return

        try:
            replied_to = (
                message.reference.resolved
                or await message.channel.fetch_message(message.reference.message_id)
            )
        except Exception as e:
            print(f"❌ [ERROR] Failed to resolve referenced message: {e}")
            return

        member = message.guild.get_member(replied_to.author.id)
        if not member:
            return

        if member.id not in self.whitelisted_members:
            return

        if message.embeds:
            embed = message.embeds[0]
            description = embed.description.lower() if embed.description else ""
            embed_color = embed.color.value if embed.color else None

            drop_type = None
            if "you caught a" in description:
                promo_emoji = promo["emoji"]
                promo_name = promo["name"]
                promo_emoji_name = promo["emoji_name"]
                if embed_color == FISH_COLOR:
                    drop_type = "fish"
                    rate = promo["fish_rate"]
                else:
                    drop_type = "catch"
                    rate = promo["catch_rate"]

                # Extract caught Pokémon name
                caught_match = re.search(r"you caught a (shiny )?(\w+)", description)
                caught_pokemon = caught_match.group(2).lower() if caught_match else ""

                # 🔥 Force drop if it's Mew
                if caught_pokemon == "mew":
                    roll = 1
                    print(f"🌟 [FORCE DROP] {member.display_name} caught a Mew!")
                    drop_type = "mew"
                    drop_msg = f"{Emojis.pink_sparkle} {member.mention} has caught a Mew! Oh? It looks like it dropped a **{promo_emoji_name}** {promo_emoji} {Emojis.pink_heart_movin}"
                else:
                    roll = random.randint(1, rate)

                print(
                    # f"🎲 [ROLL] {member.display_name} rolled {roll} (1 out of {rate})"
                )

                if roll == 1:
                    # 🛡 Don’t overwrite custom Mew message
                    if caught_pokemon != "mew":
                        drop_msg = f"{member.mention} has discovered a **{promo_emoji_name}** {promo_emoji} while {drop_type}ing! {Emojis.pink_heart_movin}"
                    print(f"🎉 {drop_msg}")

                    drop_message = await message.channel.send(drop_msg)
                    drop_message_id = drop_message.id
                    msg_link = f"[{Emojis.pink_link} Message Link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{drop_message_id})"

                    await record_item_drop(self.bot, member.id, drop_type)
                    hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

                    drop_track_embed = build_drop_track_embed(
                        bot=self.bot,
                        member=member,
                        method=drop_type,
                        promo_emoji=promo_emoji,
                        promo_emoji_name=promo_emoji_name,
                        promo_name=promo_name,
                        msg_link=msg_link,
                    )
                    await hunt_channel.send(embed=drop_track_embed)

    # 🎀 Discord event listener for new messages
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.handle_new_message(message)

    # 🎀 Discord event listener for edited messages
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.handle_edit_message(after)

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔄 Rebuilding whitelist cache...")
        self.whitelisted_members.clear()

        for guild in self.bot.guilds:
            for member in guild.members:
                role_ids = {r.id for r in member.roles}
                if (
                    HERSHEY_ROLE_ID in role_ids
                    and DONATED_ROLE_ID in role_ids
                    and ABSENT_ROLE_ID not in role_ids
                    and NON_WEEKLY_ROLE_ID not in role_ids
                ):
                    self.whitelisted_members.add(member.id)

        print(f"✅ Whitelist built with {len(self.whitelisted_members)} members.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        role_ids = {r.id for r in after.roles}
        if (
            HERSHEY_ROLE_ID in role_ids
            and DONATED_ROLE_ID in role_ids
            and ABSENT_ROLE_ID not in role_ids
            and NON_WEEKLY_ROLE_ID not in role_ids
        ):
            self.whitelisted_members.add(after.id)
        else:
            self.whitelisted_members.discard(after.id)


# ————————————————————————————————
# 🎀 Cog Setup – Adds EventWatcher cog to the bot
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(EventWatcher(bot))
