import logging
from typing import List, Dict, Any
from datetime import datetime

from core.models import Journey, Transfer, Fare

logger = logging.getLogger("oncf_bot.services.parser")

def parse_duration(duration_str: str) -> int:
    """Parses duration string like '01h30' into minutes."""
    try:
        parts = duration_str.split('h')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1] or 0)
    except (ValueError, AttributeError):
        pass
    return 0

def parse_availability_response(data: dict) -> List[Journey]:
    """
    Parses the ONCF /availability response body into a list of Journey objects.
    """
    journeys = []
    
    if not data or not data.get("body"):
        return journeys
        
    for item in data["body"]:
        try:
            # Fallback if structure varies
            dep_station = item.get("gareDepart", "Unknown")
            arr_station = item.get("gareArrivee", "Unknown")
            dep_time_raw = item.get("dateDepart", "") # Format: YYYY-MM-DDTHH:MM:SS
            arr_time_raw = item.get("dateArrivee", "")
            
            dep_time = dep_time_raw.split("T")[1][:5] if "T" in dep_time_raw else dep_time_raw
            arr_time = arr_time_raw.split("T")[1][:5] if "T" in arr_time_raw else arr_time_raw
            
            duration = item.get("duree", "00h00")
            duration_minutes = parse_duration(duration)
            
            # Extract prices. The structure often has "prix" or we extract it from first segment
            fares = Fare()
            min_price = float('inf')
            
            # In typical ONCF availability body, price info can be in 'voyageurs' or root 'prix'
            # Let's inspect 'voyageurs' first, assuming simple 1 passenger
            voyageurs = item.get("voyageurs", [])
            for voy in voyageurs:
                for tarif in voy.get("tarifs", []):
                    code = tarif.get("codeClasse") # e.g., '1' or '2'
                    price_val = tarif.get("prix", 0.0)
                    if price_val:
                        price = float(price_val)
                        if code == '1' or code == 1:
                            fares.first_class_price = price
                        elif code == '2' or code == 2:
                            fares.second_class_price = price
                        
                        if price < min_price:
                            min_price = price

            # Fallback to root 'prix' if the above doesn't exist
            if not fares.first_class_price and not fares.second_class_price:
                 for p in item.get("prix", []):
                    classe = p.get("classe")
                    val = p.get("montant")
                    if val:
                        price = float(val)
                        if classe == 1:
                            fares.first_class_price = price
                        elif classe == 2:
                            fares.second_class_price = price
                        if price < min_price:
                            min_price = price

            # Train segments and Transfers
            transfers = []
            segments = item.get("segments", [])
            
            # e.g., "700 ➔ 608"
            train_nums = " ➔ ".join([str(seg.get("numeroTrain", "")) for seg in segments])
            
            if len(segments) > 1:
                for i in range(len(segments) - 1):
                    current_seg = segments[i]
                    next_seg = segments[i+1]
                    
                    transfer_station = current_seg.get("gareArrivee", "Transfer")
                    arr_at_transfer = current_seg.get("dateArrivee", "").split("T")[-1][:5]
                    dep_from_transfer = next_seg.get("dateDepart", "").split("T")[-1][:5]
                    
                    # Calculate layover roughly in minutes
                    try:
                        arr_dt = datetime.fromisoformat(current_seg.get("dateArrivee"))
                        dep_dt = datetime.fromisoformat(next_seg.get("dateDepart"))
                        layover_minutes = int((dep_dt - arr_dt).total_seconds() / 60)
                    except Exception:
                        layover_minutes = 0
                    
                    transfers.append(Transfer(
                        station_name=transfer_station,
                        arrival_time=arr_at_transfer,
                        departure_time=dep_from_transfer,
                        layover_minutes=max(0, layover_minutes)
                    ))
            
            journey = Journey(
                departure_station=dep_station,
                arrival_station=arr_station,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration=duration,
                train_numbers=train_nums,
                fares=fares,
                transfers=transfers,
                duration_minutes=duration_minutes,
                min_price=min_price if min_price != float('inf') else 0
            )
            journeys.append(journey)
                
        except Exception as e:
            logger.warning(f"Failed to parse a journey item: {e}")
            continue
            
    return journeys

def get_best_journeys(journeys: List[Journey], limit: int = 5) -> List[Journey]:
    """
    Returns the top journeys sorted by price (ascending) then duration (ascending).
    """
    valid_journeys = [j for j in journeys if j.min_price > 0]
    # Sort primarily by min_price, secondarily by duration_minutes
    sorted_journeys = sorted(valid_journeys, key=lambda j: (j.min_price, j.duration_minutes))
    return sorted_journeys[:limit]
