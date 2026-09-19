from thefuzz import process

STATIONS = {
    "addakhla": "796",
    "aeroport_med_v": "190",
    "agadir": "745",
    "agdz": "832",
    "ain_defali": "884",
    "ain_sebaa": "213",
    "ain_taoujdate": "367",
    "asilah": "317",
    "assa": "761",
    "azemmour_halte": "625",
    "azrou": "852",
    "benguerir": "120",
    "beni_nsar_port": "660",
    "beni_nsar_ville": "662",
    "beni_mellal": "800",
    "berrechid": "183",
    "bidane": "71",
    "bouizakarne": "755",
    "boujad": "810",
    "boujdour": "794",
    "boumalne": "828",
    "bouskoura": "187",
    "bouznika": "221",
    "casa_port": "206",
    "casa_voyageurs": "200",
    "chefchaouen": "888",
    "dalia": "310",
    "dar_el_guedari": "261",
    "el_aioun": "459",
    "el_argoub": "772",
    "el_hajeb": "850",
    "el_jadida": "610",
    "el_ksar_el_kebir": "325",
    "elkelaa_mgouna": "826",
    "ennassim": "194",
    "ennouasser": "185",
    "eoufouss": "861",
    "erfoud": "862",
    "errachidia": "860",
    "errich": "858",
    "essaouira": "740",
    "facultes": "192",
    "fes": "380",
    "fnideq": "892",
    "gargarate": "778",
    "guelmima": "844",
    "guelmime": "760",
    "guercif": "441",
    "hassi_berkane": "670",
    "inezgane": "747",
    "jorf_el_melha": "882",
    "kasbah_tadla": "809",
    "kelaa_des_sragnas": "801",
    "kenitra": "250",
    "kenitra_medina": "251",
    "khenifra": "818",
    "khouribga": "167",
    "ksar_sghir": "295",
    "laayoune": "790",
    "laayoune_port": "791",
    "lalla_yto": "260",
    "lamhariz": "776",
    "l_oasis": "191",
    "marrakech": "110",
    "martil": "893",
    "matmata": "417",
    "mdaq": "890",
    "mechra_bel_ksiri": "339",
    "meknes": "363",
    "meknes_al_amir": "362",
    "melg_el_ouidane": "674",
    "melloussa_1": "299",
    "mers_sultan": "193",
    "merzouga": "870",
    "midelt": "856",
    "mohammedia": "217",
    "mrirt": "820",
    "nador_sud": "666",
    "nador_ville": "664",
    "ouarzazate": "825",
    "oued_amlil": "423",
    "oued_zem": "173",
    "oueled_rahou": "672",
    "ouezzane": "886",
    "oujda": "490",
    "oulad_khitib": "262",
    "port_tanger_med": "291",
    "rabat_agdal": "229",
    "rabat_ville": "231",
    "ras_el_ain": "155",
    "rissani": "864",
    "safi": "57",
    "sale": "237",
    "sale_tabriquet": "238",
    "sebaa_aioun": "365",
    "selouane": "668",
    "settat": "139",
    "sidi_bou_othmane": "116",
    "sidi_el_aidi": "140",
    "sidi_hajjaj": "159",
    "sidi_kacem": "350",
    "sidi_slimane_medina": "264",
    "sidi_yahia": "259",
    "skhirat": "223",
    "smara": "785",
    "souk_el_arbaa": "337",
    "tamanar": "742",
    "tamelalt": "802",
    "tan_tan": "770",
    "tan_tan_port": "775",
    "tanger": "303",
    "tanger_morora": "306",
    "taourirt": "451",
    "tarfaya": "780",
    "taza": "431",
    "tchika": "774",
    "temara": "227",
    "tetouan": "806",
    "tinerhir": "830",
    "tinjdad": "840",
    "tiznit": "750",
    "tleta_rissana": "321",
    "youssoufia": "77",
    "zag": "762",
    "zagora": "834",
    "zaouiat_chehch": "816",
}

def get_station_code(name: str) -> str:
    """Gets the station code exactly matching the key."""
    if not name:
        return None
    return STATIONS.get(name.lower().replace(" ", "_"))

def get_station_name_by_code(code: str) -> str:
    """Reverse map a station code to its display name."""
    for name, c in STATIONS.items():
        if c == code or c == str(code):
            return name.replace("_", " ").title()
    return str(code)

def find_best_matches(query: str, limit: int = 25) -> list[tuple[str, str]]:
    """
    Fuzzy match station names for autocomplete.
    Returns a list of tuples (Display Name, Station Key).
    """
    if not query:
        # Return first N stations if query is empty
        return [(k.replace("_", " ").title(), STATIONS[k]) for k in list(STATIONS.keys())[:limit]]
        
    choices = list(STATIONS.keys())
    results = process.extract(query.lower(), choices, limit=limit)
    
    # thefuzz process.extract returns a list of tuples (matched_string, score)
    # We only return matches with a reasonable score to avoid junk
    valid_results = [match for match in results if match[1] > 50]
    
    return [(match[0].replace("_", " ").title(), STATIONS[match[0]]) for match in valid_results][:limit]
