import discord
from discord import Embed, Interaction, app_commands
from discord.ext import commands

from config.constants import STAFF_ROLE_ID

# ————————————————————————————————
# 🛡️ Staff Role Check – Only trusted hands allowed!
# ————————————————————————————————
STAFF_ROLE_IDS = {STAFF_ROLE_ID, 987654321098765432}


class EmbedEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff():
        def predicate(interaction: discord.Interaction) -> bool:
            return any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles)

        return app_commands.check(predicate)

    @app_commands.command(
        name="edit_embed_desc", description="Edit the description of an embed message"
    )
    @is_staff()
    @app_commands.describe(
        channel="Channel where the message is",
        message_id="ID of the message to edit (paste raw ID, no brackets)",
        embed_index="Embed number to edit (starting from 1)",
    )
    async def edit_embed_desc(
        self,
        interaction: Interaction,
        channel: discord.TextChannel,
        message_id: str,
        embed_index: int = 1,
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            msg_id_int = int(message_id)
        except ValueError:
            await interaction.followup.send(
                "Invalid message ID format. Please provide a valid numeric ID.",
                ephemeral=True,
            )
            return

        try:
            message = await channel.fetch_message(msg_id_int)
        except Exception:
            await interaction.followup.send("Message not found.", ephemeral=True)
            return

        if not message.embeds:
            await interaction.followup.send(
                "That message has no embeds.", ephemeral=True
            )
            return

        if embed_index < 1 or embed_index > len(message.embeds):
            await interaction.followup.send(
                f"Invalid embed index. This message has {len(message.embeds)} embeds.",
                ephemeral=True,
            )
            return

        embed = message.embeds[embed_index - 1]
        original_desc = embed.description or ""

        # Now send the modal
        await interaction.followup.send_modal(
            EditEmbedModal(original_desc, message, embed_index - 1)
        )


class EditEmbedModal(discord.ui.Modal, title="Edit Embed Description"):
    def __init__(self, original_desc, message, embed_index):
        super().__init__()
        self.message = message
        self.embed_index = embed_index
        self.desc_input = discord.ui.TextInput(
            label="New Description",
            style=discord.TextStyle.paragraph,
            default=original_desc,
            required=True,
            max_length=4096,
        )
        self.add_item(self.desc_input)

    async def on_submit(self, interaction: Interaction):
        embeds = [embed.copy() for embed in self.message.embeds]
        embeds[self.embed_index].description = self.desc_input.value

        try:
            await self.message.edit(embeds=embeds)
            await interaction.response.send_message(
                "Embed description updated!", ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                "Failed to edit embed.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(EmbedEdit(bot))
