import discord
from discord import app_commands
from discord.ext import commands

from ui.views import LoginModal
from services.oncf_client import oncf_client
from core.exceptions import AuthenticationFailedError
from core.groups import train_group

class AuthCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @train_group.command(name="login", description="Authenticate with ONCF (Securely)")
    async def login(self, interaction: discord.Interaction):
        """Pops up a modal to enter ONCF credentials securely."""
        
        async def on_submit_callback(modal_interaction: discord.Interaction, email: str, password: str):
            await modal_interaction.response.defer(ephemeral=True)
            try:
                await oncf_client.login(modal_interaction.user.id, email, password)
                await modal_interaction.followup.send("✅ Successfully logged in! Your token is cached for 45 minutes.", ephemeral=True)
            except AuthenticationFailedError as e:
                await modal_interaction.followup.send(f"❌ Login failed: {e}", ephemeral=True)
            except Exception as e:
                import logging
                logging.error(f"Error in login modal: {e}", exc_info=True)
                await modal_interaction.followup.send(f"❌ An unexpected error occurred.", ephemeral=True)

        modal = LoginModal(callback=on_submit_callback)
        await interaction.response.send_modal(modal)

async def setup(bot: commands.Bot):
    await bot.add_cog(AuthCog(bot))
