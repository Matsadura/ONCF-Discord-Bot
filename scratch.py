import asyncio
import aiohttp
from core.models import AvailabilityRequest, PassengerInfo

async def main():
    payload = AvailabilityRequest(
        codeGareDepart="120", # benguerir
        codeGareArrivee="363", # meknes
        dateDepartAller="2026-09-20T00:01:01+01:00",
        listVoyageur=[PassengerInfo(codeProfilDemographique="3")]
    ).model_dump()
    print("Payload:", payload)
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.oncf-voyages.ma",
        "Referer": "https://www.oncf-voyages.ma/"
    }
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        async with session.post("https://www.oncf-voyages.ma/api/availability", json=payload) as resp:
            data = await resp.text()
            print("Response:", data)

asyncio.run(main())
