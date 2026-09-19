import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from core.exceptions import ONCFAPIError, AuthenticationFailedError

logger = logging.getLogger("oncf_bot.services.client")

class ONCFClient:
    BASE_URL = "https://www.oncf-voyages.ma/api"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.oncf-voyages.ma",
        "Referer": "https://www.oncf-voyages.ma/"
    }

    def __init__(self):
        # We don't initialize the session in __init__ because it needs an async loop
        self._session: Optional[aiohttp.ClientSession] = None
        self._token_cache: Dict[int, dict] = {} # user_id -> {"token": str, "expires_at": datetime, "client_num": str}
        self._lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # ONCF has broken SSL, so we use a custom TCP connector with ssl=False
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(connector=connector, headers=self.HEADERS)
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def login(self, discord_user_id: int, email: str, pwd: str) -> str:
        """Authenticates a user and caches their token for 45 mins."""
        session = await self.get_session()
        payload = {
            "culture": 3,
            "login": email,
            "pwd": pwd,
            "includeProfile": True,
            "unlockUrl": "https://www.oncf-voyages.ma/deblocage-compte",
            "isEntreprise": False
        }
        
        async with self._lock: # prevent spamming login for the same user concurrently
            try:
                async with session.post(f"{self.BASE_URL}/login", json=payload, timeout=10) as response:
                    if response.status != 200:
                        raise AuthenticationFailedError(f"Login failed with status {response.status}")
                    
                    data = await response.json()
                    
                    if not data.get("body") or data.get("errorCode") == 909:
                        raise AuthenticationFailedError(data.get("message", "Invalid credentials or fields"))
                        
                    token = data["body"].get("token")
                    if not token:
                        raise AuthenticationFailedError("No token returned in response body")
                    
                    # Cache the token for 45 minutes
                    expires_at = datetime.now() + timedelta(minutes=45)
                    self._token_cache[discord_user_id] = {
                        "token": token,
                        "expires_at": expires_at,
                        "client_num": data["body"].get("numeroClient", None) # Might be needed for Carte Jeune booking
                    }
                    return token
                    
            except asyncio.TimeoutError:
                raise AuthenticationFailedError("Login request timed out")
            except aiohttp.ClientError as e:
                raise AuthenticationFailedError(f"Network error during login: {e}")

    def get_token(self, discord_user_id: int) -> Optional[str]:
        """Gets a valid token from cache if it exists."""
        cache_entry = self._token_cache.get(discord_user_id)
        if cache_entry and cache_entry["expires_at"] > datetime.now():
            return cache_entry["token"]
        return None

    def get_client_num(self, discord_user_id: int) -> Optional[str]:
        """Gets the client number from cache if valid."""
        cache_entry = self._token_cache.get(discord_user_id)
        if cache_entry and cache_entry["expires_at"] > datetime.now():
            return cache_entry.get("client_num")
        return None

    async def search_availability(self, payload: dict) -> dict:
        """Queries the ONCF availability endpoint."""
        session = await self.get_session()
        
        # Throttling to be polite to the ONCF gateway
        await asyncio.sleep(0.4)
        
        try:
            async with session.post(f"{self.BASE_URL}/availability", json=payload, timeout=15) as response:
                if response.status != 200:
                    raise ONCFAPIError(f"API returned status {response.status}")
                
                # The response could be text or json. Let's try json
                try:
                    data = await response.json()
                except Exception:
                    text = await response.text()
                    raise ONCFAPIError(f"Failed to parse JSON. Response: {text[:200]}")

                if not data or not data.get("body"):
                    raise ONCFAPIError(f"Invalid API response: {data.get('message', 'No body in response')}")
                
                return data
                
        except asyncio.TimeoutError:
            raise ONCFAPIError("Availability request timed out")
        except aiohttp.ClientError as e:
            raise ONCFAPIError(f"Network error during availability check: {e}")

# Global instance to be used across cogs
oncf_client = ONCFClient()
