import asyncio
import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("oncf_bot")

class ONCFBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load cogs here
        await self.load_extension("cogs.train")
        
        # Sync slash commands
        logger.info("Syncing commands...")
        await self.tree.sync()
        logger.info("Commands synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

async def main():
    bot = ONCFBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
