import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

from core.stations import find_best_matches
from core.models import AvailabilityRequest, PassengerInfo
from services.oncf_client import oncf_client
from services.parser import parse_availability_response, get_best_journeys
from ui.embeds import build_journey_embed, build_comparison_embed, build_error_embed
from ui.views import JourneyPaginator
from core.exceptions import ONCFAPIError
from core.groups import train_group

logger = logging.getLogger("oncf_bot.cogs.train")

class TrainCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def station_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        matches = find_best_matches(current)
        return [app_commands.Choice(name=name, value=code) for name, code in matches][:25]

    @train_group.command(name="search", description="Search for train journeys")
    @app_commands.autocomplete(origin=station_autocomplete, destination=station_autocomplete)
    async def search(
        self, 
        interaction: discord.Interaction, 
        origin: str, 
        destination: str, 
        date: str = None, 
        youth_card: bool = False
    ):
        await interaction.response.defer()
        
        try:
            if not date:
                date_obj = datetime.now()
            else:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await interaction.followup.send(embed=build_error_embed("Invalid date format. Use YYYY-MM-DD."))
            return

        date_str = date_obj.strftime("%Y-%m-%dT00:01:01+01:00")
        
        token = ""
        client_num = None
        if youth_card:
            token = oncf_client.get_token(interaction.user.id)
            client_num = oncf_client.get_client_num(interaction.user.id)
            if not token:
                await interaction.followup.send(embed=build_error_embed("You must login first to use the Youth Card. Use `/train login`."))
                return

        passenger = PassengerInfo(
            numeroClient=client_num if youth_card else None,
            codeTarif="JF" if youth_card else None,
            codeProfilDemographique="2" if youth_card else "3"
        )

        payload = AvailabilityRequest(
            codeGareDepart=origin,
            codeGareArrivee=destination,
            dateDepartAller=date_str,
            isTarifReduit=youth_card,
            listVoyageur=[passenger],
            token=token,
            isActive=youth_card
        ).model_dump()

        try:
            response_data = await oncf_client.search_availability(payload)
            journeys = parse_availability_response(response_data)
            
            if not journeys:
                await interaction.followup.send(embed=build_error_embed("No journeys found for this route and date."))
                return

            view = JourneyPaginator(journeys, youth_card)
            
            # Initial message setup
            journey = view.displayed_journeys[0]
            embed = build_journey_embed(journey, youth_card)
            embed.set_footer(text=f"Result 1 of {len(view.displayed_journeys)}")
            
            is_fastest = journey.duration_minutes == min(j.duration_minutes for j in journeys)
            is_cheapest = journey.min_price > 0 and journey.min_price == min(j.min_price for j in journeys if j.min_price > 0)
            
            badges = []
            if is_fastest: badges.append("⚡ Fastest")
            if is_cheapest: badges.append("💰 Best Price")
            if badges:
                embed.description = " | ".join(badges)
            
            await interaction.followup.send(embed=embed, view=view)

        except ONCFAPIError as e:
            await interaction.followup.send(embed=build_error_embed(f"ONCF API Error: {e}"))
        except Exception as e:
            logger.error(f"Error in search: {e}", exc_info=True)
            await interaction.followup.send(embed=build_error_embed("An unexpected error occurred."))

    @train_group.command(name="compare", description="Multi-Day Deal Finder")
    @app_commands.autocomplete(origin=station_autocomplete, destination=station_autocomplete)
    @app_commands.describe(days="Number of days to search (1-7)")
    async def compare(
        self,
        interaction: discord.Interaction,
        origin: str,
        destination: str,
        start_date: str,
        days: int = 3,
        youth_card: bool = False
    ):
        if days < 1 or days > 7:
            await interaction.response.send_message(embed=build_error_embed("Days must be between 1 and 7."), ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            await interaction.followup.send(embed=build_error_embed("Invalid date format. Use YYYY-MM-DD."))
            return

        token = ""
        client_num = None
        if youth_card:
            token = oncf_client.get_token(interaction.user.id)
            client_num = oncf_client.get_client_num(interaction.user.id)
            if not token:
                await interaction.followup.send(embed=build_error_embed("You must login first to use the Youth Card. Use `/train login`."))
                return

        passenger = PassengerInfo(
            numeroClient=client_num if youth_card else None,
            codeTarif="JF" if youth_card else None,
            codeProfilDemographique="2" if youth_card else "3"
        )

        all_journeys = []
        
        for i in range(days):
            current_date = start_date_obj + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%dT00:01:01+01:00")
            
            payload = AvailabilityRequest(
                codeGareDepart=origin,
                codeGareArrivee=destination,
                dateDepartAller=date_str,
                isTarifReduit=youth_card,
                listVoyageur=[passenger],
                token=token,
                isActive=youth_card
            ).model_dump()

            try:
                response_data = await oncf_client.search_availability(payload)
                journeys = parse_availability_response(response_data)
                all_journeys.extend(journeys)
            except Exception as e:
                logger.warning(f"Failed to fetch for {current_date}: {e}")
                
        if not all_journeys:
            await interaction.followup.send(embed=build_error_embed("No journeys found for this route across the selected days."))
            return
            
        best_journeys = get_best_journeys(all_journeys, limit=5)
        
        # Get actual station names
        origin_name = best_journeys[0].departure_station if best_journeys else origin
        dest_name = best_journeys[0].arrival_station if best_journeys else destination
        title = f"{origin_name} to {dest_name} from {start_date_obj.strftime('%b %d')}"
        
        embed = build_comparison_embed(title, best_journeys, days)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TrainCog(bot))
