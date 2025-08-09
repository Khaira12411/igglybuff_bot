import asyncio
import random
import re
from typing import Any, Dict
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from cogs.straymons.promo_refresher import promo_cache  # 🎀 Import existing promo cache
from config.guild_ids import *
from config.straymons.constants import *
from config.straymons.emojis import Emojis
from utils.record_drop import record_item_drop
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
        self.personal_channel_cache: Dict[int, int] = {}  # member_id -> channel_id
        self.personal_channels: Dict[int, int] = {}  # user_id -> channel_id
        self.usernames: Dict[int, str] = {}  # user_id -> display_name
        self.reverse_usernames: Dict[str, int] = {}  # display_name -> user_id

    # Build or rebuild reverse username cache from current usernames

    def is_straymons_guild(self, guild: discord.Guild | None):
        return guild and guild.id == STRAYMONS_GUILD_ID

    def build_reverse_username_cache(self):
        self.reverse_usernames = {
            username.lower(): user_id for user_id, username in self.usernames.items()
        }

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
        if not message.guild or message.guild.id != STRAYMONS_GUILD_ID:
            return

        if message.author.id != POKEMEOW_ID:
            return

        if not promo_cache.is_promo_active():
            return

        promo = promo_cache.promo
        await self.process_hershey_drops(message, promo)

    async def process_npc_drops(self, message: discord.Message, promo: Dict[str, Any]):
        def extract_username_and_pokecoins(content: str):
            # Extract username inside ** **
            username_match = re.search(r":\S+:\s\*\*(.+?)\*\*\swon the battle", content)
            username = username_match.group(1).lower() if username_match else None

            # Check for PokéCoins amount like "1,180 PokeCoins"
            pokecoin_match = re.search(r"([\d,]+) PokeCoins", content)
            pokecoin_amount = (
                int(pokecoin_match.group(1).replace(",", ""))
                if pokecoin_match
                else None
            )
            pokecoin_present = pokecoin_amount is not None

            return username, pokecoin_present, pokecoin_amount

        username, has_pokecoin, pokecoin_amount = extract_username_and_pokecoins(
            message.content
        )
        if not username:
            # Could log message content once or twice here for inspection
            return

        user_id = self.reverse_usernames.get(username)
        # print(f"[DEBUG] Cached username map: {self.reverse_usernames}")

        if not user_id:
            print(f"⚠️ [WARN] Username '{username}' not in cached usernames.")
            return

        member = message.guild.get_member(user_id)
        if not member:
            print(f"⚠️ [WARN] Member with ID {user_id} not found in guild.")
            return

        if member.id not in self.whitelisted_members:
            return

        # If PokéCoins mentioned, you can do something here

        promo_emoji = promo["emoji"]
        promo_name = promo["name"]
        promo_emoji_name = promo["emoji_name"]
        drop_type = "npc"
        roll = random.randint(1, promo["battle_rate"])
        rate = promo["battle_rate"]

        print(f"🎲 [ROLL] {member.display_name} rolled {roll} (1 out of {rate})")

        if roll == 1:
            drop_msg = f"{member.mention} has discovered a **{promo_emoji_name}** {promo_emoji} from battle! {Emojis.pink_heart_movin}"
            drop_msg_logs = f"{member.display_name} has discovered a **{promo_emoji_name}** while {drop_type}ing!"

            print(f"🎉 {drop_msg_logs}")
            drop_message = await message.channel.send(drop_msg)
            drop_message_id = drop_message.id
            msg_link = f"[{Emojis.pink_link} Message Link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{drop_message_id})"
            await record_item_drop(self.bot, member.id, drop_type)
            hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

            drop_track_embed = await build_drop_track_embed(
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
        if not message.guild or message.guild.id != STRAYMONS_GUILD_ID:
            return
        if not message.reference:
            return

        # 🌸 Add jitter to reduce burst API calls
        await asyncio.sleep(random.uniform(0.6, 1.2))

        now = asyncio.get_event_loop().time()

        # Check if embed description contains Mew for bypass
        description = ""
        if message.embeds:
            embed = message.embeds[0]
            description = embed.description.lower() if embed.description else ""

        is_mew = "**mew**" in description or "**shiny mew**" in description

        # Soft cooldown: per-user instead of global
        if not hasattr(self, "last_fetch_per_user"):
            self.last_fetch_per_user = {}

        member_id_for_cooldown = None
        if message.reference and message.reference.resolved:
            member_id_for_cooldown = message.reference.resolved.author.id
        elif message.reference:
            try:
                ref_msg = await message.channel.fetch_message(
                    message.reference.message_id
                )
                member_id_for_cooldown = ref_msg.author.id
            except:
                pass

        if member_id_for_cooldown is not None:
            last_ts = self.last_fetch_per_user.get(member_id_for_cooldown, 0.0)
            if not is_mew and now - last_ts < 1.0:
                print(
                    f"[COOLDOWN] Skipping drop for user {member_id_for_cooldown} due to cooldown."
                )
                return  # cooldown for this user only
            self.last_fetch_per_user[member_id_for_cooldown] = now

        try:
            replied_to = message.reference.resolved
            if not replied_to:
                replied_to = await message.channel.fetch_message(
                    message.reference.message_id
                )
        except discord.HTTPException as e:
            if e.status == 429:
                print(
                    f"⏳ [WAIT] [HERSHEY] Rate limited when fetching reply! Backing off... (429)"
                )
                await asyncio.sleep(2.5)
            else:
                print(f"❌ [ERROR] [HERSHEY] Failed to fetch referenced message: {e}")
            return
        except Exception as e:
            print(f"❌ [ERROR] [HERSHEY] Unexpected error: {e}")
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
            caught_pokemon = ""  # Initialize safely outside conditional

            # Detect Mew anywhere in the description first
            if "mew" in description:
                caught_pokemon = "mew"
                print(f"[DETECT] Mew detected in message for {member.display_name}.")

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
                print(
                    f"[ROLL] Rolling for drop for {member.display_name} with rate {rate}."
                )

            # 🔥 Force drop if it's Mew
            if caught_pokemon == "mew":
                roll = 1
                drop_type = "mew"
                promo_emoji = promo["emoji"]
                promo_name = promo["name"]
                promo_emoji_name = promo["emoji_name"]
                drop_msg = (
                    f"{Emojis.pink_sparkle} {member.mention} has caught a Mew! "
                    f"Oh? It looks like it dropped a **{promo_emoji_name}** {promo_emoji} {Emojis.pink_heart_movin}"
                )
                drop_msg_logs = (
                    f"{member.display_name} caught a Mew and got a forced drop!"
                )
                print(f"🌟 [FORCE DROP] {drop_msg_logs}")
            else:
                roll = random.randint(1, rate)
                print(
                    f"[ROLL RESULT] Rolled {roll} for {member.display_name} (1 means drop)."
                )

            if roll == 1:
                if caught_pokemon != "mew":
                    drop_msg = f"{member.mention} has discovered a **{promo_emoji_name}** {promo_emoji} while {drop_type}ing! {Emojis.pink_heart_movin}"
                    drop_msg_logs = f"{member.display_name} has discovered a **{promo_emoji_name}** while {drop_type}ing!"
                    print(f"🎉 {drop_msg_logs}")

                drop_message = await message.channel.send(drop_msg)
                drop_message_id = drop_message.id
                msg_link = f"[{Emojis.pink_link} Message Link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{drop_message_id})"

                await record_item_drop(self.bot, member.id, drop_type)
                hunt_channel = message.guild.get_channel(HUNT_CHANNEL_ID)

                drop_track_embed = await build_drop_track_embed(
                    bot=self.bot,
                    member=member,
                    method=drop_type,
                    promo_emoji=promo_emoji,
                    promo_emoji_name=promo_emoji_name,
                    promo_name=promo_name,
                    msg_link=msg_link,
                )
                await hunt_channel.send(embed=drop_track_embed)
            else:
                print(f"[NO DROP] No drop this roll for {member.display_name}.")

    # ————————————————————————————————
    # 🎀 Discord event listener for new messages
    # ————————————————————————————————
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.guild.id != STRAYMONS_GUILD_ID:
            return
        if message.channel.id not in self.personal_channels.values():
            return

        await self.handle_new_message(message)

    # 🎀 Discord event listener for edited messages
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        if not after.guild or after.guild.id != STRAYMONS_GUILD_ID:
            return
        if after.channel.id not in self.personal_channels.values():
            return
        if after.author.id != POKEMEOW_ID:
            return
        await self.handle_edit_message(after)

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔄 Rebuilding whitelist and personal channel caches...")

        self.whitelisted_members.clear()
        self.usernames = {}
        self.personal_channels = {}

        for guild in self.bot.guilds:
            if not self.is_straymons_guild(guild):
                continue
            for member in guild.members:
                role_ids = {r.id for r in member.roles}
                if (
                    HERSHEY_ROLE_ID in role_ids
                    and DONATED_ROLE_ID in role_ids
                    and ABSENT_ROLE_ID not in role_ids
                    and NON_WEEKLY_ROLE_ID not in role_ids
                ):
                    self.whitelisted_members.add(member.id)
                    self.usernames[member.id] = member.name.lower()
        # After loop:
        self.build_reverse_username_cache()

        # Load personal channels ONLY for whitelisted members
        async with self.bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, channel_id FROM straymons_members")
            for row in rows:
                if row["user_id"] in self.whitelisted_members:
                    self.personal_channels[row["user_id"]] = row["channel_id"]

        print(
            f"✅ Whitelist: {len(self.whitelisted_members)}, Channels: {len(self.personal_channels)}"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild.id != STRAYMONS_GUILD_ID:
            return

        role_ids = {r.id for r in after.roles}

        if (
            HERSHEY_ROLE_ID in role_ids
            and DONATED_ROLE_ID in role_ids
            and ABSENT_ROLE_ID not in role_ids
            and NON_WEEKLY_ROLE_ID not in role_ids
        ):
            self.whitelisted_members.add(after.id)
            # Update username if changed
            if self.usernames.get(after.id) != after.name.lower():
                self.usernames[after.id] = after.name.lower()
                self.build_reverse_username_cache()
        else:
            self.whitelisted_members.discard(after.id)
            # Remove username if present
            if after.id in self.usernames:
                self.usernames.pop(after.id)
                self.build_reverse_username_cache()


# ————————————————————————————————
# 🎀 Cog Setup – Adds EventWatcher cog to the bot
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(EventWatcher(bot))
