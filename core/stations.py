from thefuzz import process

# Common Moroccan cities to station codes
STATIONS = {
    "benguerir": "120",
    "meknes": "363",
    "meknes_amir_abdelkader": "362",
    "mohammedia": "217",
    "casa_voyageurs": "200",
    "casa_port": "215",
    "casa_oasis": "203",
    "rabat_agdal": "229",
    "rabat_ville": "230",
    "marrakech": "110",
    "tanger": "303",
    "fes": "372",
    "oujda": "321",
    "kenitra": "237",
    "el_jadida": "241",
    "settat": "126",
    "khouribga": "142",
    "safi": "131",
    "nador_ville": "505",
    "sale_ville": "233",
    "sale_tabriquet": "234",
    "aeroport_mohammed_v": "212",
}

def get_station_code(name: str) -> str:
    """Gets the station code exactly matching the key."""
    if not name:
        return None
    return STATIONS.get(name.lower().replace(" ", "_"))

def find_best_matches(query: str, limit: int = 25) -> list[tuple[str, str]]:
    """
    Fuzzy match station names for autocomplete.
    Returns a list of tuples (Display Name, Station Key).
    """
    if not query:
        # Return first N stations if query is empty
        return [(k.replace("_", " ").title(), k) for k in list(STATIONS.keys())[:limit]]
        
    choices = list(STATIONS.keys())
    results = process.extract(query.lower(), choices, limit=limit)
    
    # thefuzz process.extract returns a list of tuples (matched_string, score)
    # We only return matches with a reasonable score to avoid junk
    valid_results = [match for match in results if match[1] > 50]
    
    return [(match[0].replace("_", " ").title(), match[0]) for match in valid_results][:limit]
