import random
import re
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from cogs.promo_refresher import promo_cache  # 🎀 Import existing promo cache
from config.constants import FISH_COLOR, HUNT_CHANNEL_ID, PARFAIT_ROLE_ID, POKEMEOW_ID
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

    # 💌 Handle new messages, only from PokéMeow bot
    async def handle_new_message(self, message: discord.Message):
        print(
            f"🎀 [EVENT WATCHER] on_message from {message.author} (ID: {message.author.id})"
        )
        if message.author.id != POKEMEOW_ID:
            print("💤 [SKIP] Message not from PokéMeow.")
            return

        print("✨ [MESSAGE WATCHER] Processing PokéMeow message...")

        if not promo_cache.is_promo_active():
            print("💤 [SKIP] No active promo, skipping plushie drop check.")
            return

        promo = promo_cache.promo
        await self.process_npc_drops(message, promo)

    # 💌 Handle edited messages for parfait drops
    async def handle_edit_message(self, message: discord.Message):
        print(
            f"🎀 [EVENT WATCHER] on_message_edit from {message.author} (ID: {message.author.id})"
        )
        if message.author.id != POKEMEOW_ID:
            print("💤 [SKIP] Edited message not from PokéMeow.")
            return

        print("✨ [EDIT WATCHER] Processing PokéMeow edited message...")

        if not promo_cache.is_promo_active():
            print("💤 [SKIP] No active promo, skipping parfait drop check.")
            return

        promo = promo_cache.promo
        await self.process_parfait_drops(message, promo)

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

            parfait_role = discord.utils.get(member.roles, id=PARFAIT_ROLE_ID)
            if not parfait_role:
                print(f"💤 [SKIP] Member {member} lacks parfait role.")
                return
            promo_emoji = promo["emoji"]
            promo_name = promo["name"]
            promo_emoji_name = promo["emoji_name"]
            drop_type = "npc"
            roll = random.randint(1, promo["battle_rate"])
            print(f"🎲 [ROLL] Rolled {roll} for NPC battle drop (1 means success).")
            if roll == 1:
                drop_msg = f"{member.mention} has discovered a {promo_emoji} from battle! {Emojis.pink_heart_movin}"
                print(f"🎉 {drop_msg}")
                await message.channel.send(drop_msg)
                await record_item_drop(self.bot, member.id, drop_type)
                hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

                drop_track_embed = build_drop_track_embed(
                    member=member,
                    method="battle",
                    promo_emoji=promo_emoji,
                    promo_emoji_name=promo_emoji_name,
                    promo_name=promo_name,
                )
                await hunt_channel.send(embed=drop_track_embed)

    # 🎯 Process parfait reply messages to check for fish or catch plushie drops
    async def process_parfait_drops(
        self, message: discord.Message, promo: Dict[str, Any]
    ):
        if not message.guild or not message.reference:
            print("💤 [SKIP] No guild or missing message reference for parfait drop.")
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
            print("💤 [SKIP] Replied member not found in guild.")
            return

        parfait_role = discord.utils.get(member.roles, id=PARFAIT_ROLE_ID)
        if not parfait_role:
            print("💤 [SKIP] Member lacks parfait role.")
            return

        if message.embeds:
            embed = message.embeds[0]
            description = embed.description.lower() if embed.description else ""
            embed_color = embed.color.value if embed.color else None

            if embed_color is not None:
                print(f"💗 [DEBUG] Embed color: #{embed_color:06x}")
            else:
                print("💗 [DEBUG] Embed has no color.")

            drop_type = None
            if "you caught a" in description:
                print("✨ [DEBUG] Detected 'you caught a' phrase in embed description.")
                promo_emoji = promo["emoji"]
                promo_name = promo["name"]
                promo_emoji_name = promo["emoji_name"]
                if embed_color == FISH_COLOR:
                    drop_type = "fish"
                    rate = promo["fish_rate"]
                    print(
                        f"💗 [DEBUG] Color matches FISH_COLOR ({FISH_COLOR:#06x}), drop_type = fish."
                    )
                else:
                    drop_type = "catch"
                    rate = promo["catch_rate"]
                    print(
                        f"💗 [DEBUG] Color does NOT match FISH_COLOR ({FISH_COLOR:#06x}), drop_type = catch."
                    )

                roll = random.randint(1, rate)
                print(
                    f"🎲 [ROLL] Rolled {roll} for {drop_type} drop (1 means success)."
                )
                if roll == 1:
                    drop_msg = f"{member.mention} has discovered a {promo_emoji} while {drop_type}ing! {Emojis.pink_heart_movin}"
                    print(f"🎉 {drop_msg}")
                    await message.channel.send(drop_msg)
                    await record_item_drop(self.bot, member.id, drop_type)
                    hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

                    drop_track_embed = build_drop_track_embed(
                        member=member,
                        method=drop_type,
                        promo_emoji=promo_emoji,
                        promo_emoji_name=promo_emoji_name,
                        promo_name=promo_name,
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


# ————————————————————————————————
# 🎀 Cog Setup – Adds EventWatcher cog to the bot
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(EventWatcher(bot))
