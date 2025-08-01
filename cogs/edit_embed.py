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
        channel="Channel where the message is", message_id="ID of the message to edit"
    )
    async def edit_embed_desc(
        self, interaction: Interaction, channel: discord.TextChannel, message_id: int
    ):
        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            await interaction.response.send_message(
                "Message not found.", ephemeral=True
            )
            return

        if not message.embeds:
            await interaction.response.send_message(
                "That message has no embeds.", ephemeral=True
            )
            return

        embed = message.embeds[0]
        original_desc = embed.description or ""

        # Ask user for new description input with the original as placeholder
        # Discord slash commands don’t support placeholders in inputs directly,
        # so instead we can just show original desc in the prompt message

        await interaction.response.send_modal(EditEmbedModal(original_desc, message))


class EditEmbedModal(discord.ui.Modal, title="Edit Embed Description"):
    def __init__(self, original_desc, message):
        super().__init__()
        self.message = message
        self.desc_input = discord.ui.TextInput(
            label="New Description",
            style=discord.TextStyle.paragraph,
            default=original_desc,
            required=True,
            max_length=4096,
        )
        self.add_item(self.desc_input)

    async def on_submit(self, interaction: Interaction):
        embed = self.message.embeds[0]
        embed.description = self.desc_input.value

        try:
            await self.message.edit(embed=embed)
            await interaction.response.send_message(
                "Embed description updated!", ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                "Failed to edit embed.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(EmbedEdit(bot))
