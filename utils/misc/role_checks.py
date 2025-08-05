from discord.ext import commands

from config.straymons.constants import *


# 🌸──────────────────────────────────────────────
# 💖 Custom Exception Classes (Pink & Playful!) 💖
# ──────────────────────────────────────────────🌸
class ClanStaffCheckFailure(commands.CheckFailure):
    pass


class ClanMemberCheckFailure(commands.CheckFailure):
    pass


class OwnerCheckFailure(commands.CheckFailure):
    pass


# 🌷──────────────────────────────────────────────
# 💌 Error Messages – Straymons Edition 💌
# ──────────────────────────────────────────────🌷
ERROR_MESSAGES = {
    "straymons": {
        "clan_staff": "💖 You need the `🐾 Clan Staff` role to use this command! ✨",
        "clan_member": "🎀 Only members of the Straymons can do this~ 🌸",
        "owner": "👑 This command is reserved for the Clan Owner! 💞",
    },
}


# 🩷──────────────────────────────────────────────
# 🌟 Role-Based Checks for Straymons Server 🌟
# ──────────────────────────────────────────────🩷
def clan_staff_only():
    async def predicate(ctx):
        if STAFF_ROLE_ID not in [role.id for role in ctx.author.roles]:
            raise ClanStaffCheckFailure(ERROR_MESSAGES["straymons"]["clan_staff"])
        return True

    return commands.check(predicate)


def clan_member_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if STRAYMONS_ROLE_ID not in user_roles:
            raise ClanMemberCheckFailure(ERROR_MESSAGES["straymons"]["clan_member"])
        return True

    return commands.check(predicate)


def owner_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if OWNER_ROLE_ID not in user_roles:
            raise OwnerCheckFailure(ERROR_MESSAGES["straymons"]["owner"])
        return True

    return commands.check(predicate)
