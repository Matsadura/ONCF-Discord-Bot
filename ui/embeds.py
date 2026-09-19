import discord
from typing import List
from core.models import Journey

def build_error_embed(message: str) -> discord.Embed:
    embed = discord.Embed(title="❌ Error", description=message, color=discord.Color.red())
    return embed

def build_journey_embed(journey: Journey, is_youth_card: bool = False) -> discord.Embed:
    color = discord.Color.green() if is_youth_card else discord.Color.blue()
    embed = discord.Embed(
        title=f"🚆 {journey.departure_station} ➔ {journey.arrival_station}",
        color=color
    )
    
    # Time and Duration
    embed.add_field(name="Departure", value=f"`{journey.departure_time}`", inline=True)
    embed.add_field(name="Arrival", value=f"`{journey.arrival_time}`", inline=True)
    embed.add_field(name="Duration", value=f"⏳ {journey.duration}", inline=True)
    
    # Train numbers
    embed.add_field(name="Train(s)", value=f"🚂 {journey.train_numbers}", inline=False)
    
    # Fares
    fares_str = ""
    if journey.fares.second_class_price:
        fares_str += f"**2nd Class:** {journey.fares.second_class_price} MAD\n"
    if journey.fares.first_class_price:
        fares_str += f"**1st Class:** {journey.fares.first_class_price} MAD"
        
    if not fares_str:
        fares_str = "Price unavailable"
        
    embed.add_field(name="💰 Price" + (" (Carte Jeune)" if is_youth_card else ""), value=fares_str, inline=True)
    
    # Transfers
    if journey.transfers:
        transfers_str = ""
        for t in journey.transfers:
            transfers_str += f"🔄 **{t.station_name}** (Layover: {t.layover_minutes} min)\n"
        embed.add_field(name="Transfers", value=transfers_str, inline=False)
    else:
        embed.add_field(name="Transfers", value="Direct Train", inline=False)
        
    return embed

def build_comparison_embed(title: str, journeys: List[Journey], days: int) -> discord.Embed:
    embed = discord.Embed(title=f"📊 Multi-Day Deal Finder ({days} Days)", description=title, color=discord.Color.gold())
    
    if not journeys:
        embed.description = "No deals found for this timeframe."
        return embed

    for i, j in enumerate(journeys[:5]):
        details = f"🕒 {j.departure_time} - {j.arrival_time} (⏳ {j.duration})\n"
        if j.transfers:
            details += f"🔄 {len(j.transfers)} transfer(s)\n"
        else:
            details += "✅ Direct\n"
        details += f"💰 **{j.min_price} MAD**"
        
        embed.add_field(name=f"#{i+1} | {j.departure_station} ➔ {j.arrival_station}", value=details, inline=False)
        
    embed.set_footer(text="Top 5 cheapest & fastest options across the timeframe.")
    return embed
