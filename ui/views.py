import discord
from typing import List, Callable
from ui.embeds import build_journey_embed
from core.models import Journey

class JourneyPaginator(discord.ui.View):
    def __init__(self, journeys: List[Journey], is_youth_card: bool = False):
        super().__init__(timeout=300)
        self.journeys = journeys
        self.is_youth_card = is_youth_card
        self.current_page = 0
        self.direct_only = False
        
        # Original copy to restore after filtering
        self._all_journeys = journeys.copy()
        
        self.update_buttons()

    @property
    def displayed_journeys(self) -> List[Journey]:
        if self.direct_only:
            return [j for j in self._all_journeys if not j.transfers]
        return self._all_journeys

    def update_buttons(self):
        total_pages = len(self.displayed_journeys)
        self.btn_prev.disabled = self.current_page == 0
        self.btn_next.disabled = self.current_page >= total_pages - 1
        
        # Update label for filter
        self.btn_filter.label = "Show All" if self.direct_only else "Direct Trains Only"
        self.btn_filter.style = discord.ButtonStyle.green if self.direct_only else discord.ButtonStyle.secondary
        
        if total_pages <= 1:
            self.btn_next.disabled = True
            self.btn_prev.disabled = True

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.primary, custom_id="prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, custom_id="next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await self.update_message(interaction)
        
    @discord.ui.button(label="Direct Trains Only", style=discord.ButtonStyle.secondary, custom_id="filter")
    async def btn_filter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.direct_only = not self.direct_only
        self.current_page = 0 # reset pagination
        self.update_buttons()
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        journeys = self.displayed_journeys
        if not journeys:
            embed = discord.Embed(title="No Trains Found", description="No direct trains available for this route.", color=discord.Color.orange())
            await interaction.response.edit_message(embed=embed, view=self)
            return
            
        journey = journeys[self.current_page]
        embed = build_journey_embed(journey, self.is_youth_card)
        embed.set_footer(text=f"Result {self.current_page + 1} of {len(journeys)}")
        
        # Add Badges if it's the fastest or cheapest among the displayed
        if len(journeys) > 1:
            is_fastest = journey.duration_minutes == min(j.duration_minutes for j in journeys)
            is_cheapest = journey.min_price > 0 and journey.min_price == min(j.min_price for j in journeys if j.min_price > 0)
            
            badges = []
            if is_fastest: badges.append("⚡ Fastest")
            if is_cheapest: badges.append("💰 Best Price")
            
            if badges:
                embed.description = " | ".join(badges)
                
        await interaction.response.edit_message(embed=embed, view=self)

class LoginModal(discord.ui.Modal, title="ONCF Authentication"):
    email = discord.ui.TextInput(
        label="Email",
        placeholder="votre.email@example.com",
        style=discord.TextStyle.short,
        required=True
    )
    password = discord.ui.TextInput(
        label="Password",
        placeholder="••••••••",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.email.value, self.password.value)
