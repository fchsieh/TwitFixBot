import os

from dotenv import load_dotenv

from discord_client import discord_client
from packages import config

if __name__ == "__main__":
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # init config
    config.init()

    app = discord_client.DiscordClient()
    app.run(
        os.environ.get("DISCORD_TOKEN"),
        log_handler=None,  # suppress handler from discord.py
    )
