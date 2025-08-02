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

        # print(f"🎲 [ROLL] {member.display_name} rolled {roll} (1 out of {rate})")

        if roll == 1:
            drop_msg = f"{member.mention} has discovered a **{promo_emoji_name}** {promo_emoji} from battle! {Emojis.pink_heart_movin}"
            print(f"🎉 {drop_msg}")
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
        if message.guild.id != STRAYMONS_GUILD_ID:
            return

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

                description_clean = description.lower().replace("**", "")

                caught_match = re.search(
                    r"you caught a\s+(?::\w+:)?\s*(shiny )?(\w+)", description_clean
                )
                caught_pokemon = caught_match.group(2).lower() if caught_match else ""

                # Debug output
                # print(f"[DEBUG] Cleaned description: {description_clean}")
                # print(f"[DEBUG] Matched Pokémon: {caught_pokemon}")

                # 🔥 Force drop if it's Mew
                if caught_pokemon == "mew":
                    roll = 1
                    print(f"🌟 [FORCE DROP] {member.display_name} caught a Mew!")
                    drop_type = "mew"
                    drop_msg = (
                        f"{Emojis.pink_sparkle} {member.mention} has caught a Mew! "
                        f"Oh? It looks like it dropped a **{promo_emoji_name}** {promo_emoji} {Emojis.pink_heart_movin}"
                    )

                else:
                    roll = random.randint(1, rate)

                # print(f"🎲 [ROLL] {member.display_name} rolled {roll} (1 out of {rate})")

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

    # 🎀 Discord event listener for new messages
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only listen to messages in personal channels of whitelisted
        if message.guild.id != STRAYMONS_GUILD_ID:
            return
        if message.channel.id not in self.personal_channels.values():
            return

        await self.handle_new_message(message)

    # 🎀 Discord event listener for edited messages
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or after.guild.id != STRAYMONS_GUILD_ID:
            return
        # Only listen to messages in personal channels of whitelisted members
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
