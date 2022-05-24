import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

import discord_client
import twitter_client

AVATAR_IMG = "./avatar.jpg"  # default image for webhook
LOG_NAME = "twitfix.log"

mp4_list = [
    "https://i.imgur.com/cD9zcNa.mp4",
    "https://i.imgur.com/rMGBqDw.mp4",
    "https://i.imgur.com/0qMjkp0.mp4",
    "https://i.imgur.com/1btGCc8.mp4",
    "https://i.imgur.com/3owYjoS.mp4",
]
gif_list = [
    "https://i.imgur.com/q8ia35n.gif",
    "https://i.imgur.com/pEX7UOb.gif",
    "https://i.imgur.com/Fs3G21A.gif",
    "https://i.imgur.com/y4yOpVF.gif",
    "https://i.imgur.com/DKXhr5T.gif",
]
cmd_table = {
    "help": "Output this help message",
    "set_avatar <url_link>": "Change webhook avatar",
    "set_name <name>": "Change webhook name",
    "get_avatar": "Get current webhook avatar",
    "get_name": "Get current webhook name ",
}


class GLOBAL:
    def __init__(
        self,
        LOGGER=None,
        BOT_NAME="",
        WEBHOOK_NAME="",
        WEBHOOK_AVATAR=None,
        mp4_list=[],
        gif_list=[],
        cmd_table={},
        TWITTER_CLI=None,
        DISCORD_TOKEN="",
        DISCORD_CLI=None,
    ):
        # Log-related
        self.LOGGER = LOGGER
        # Webhook-related
        self.BOT_NAME = BOT_NAME
        self.WEBHOOK_NAME = WEBHOOK_NAME
        self.WEBHOOK_AVATAR = WEBHOOK_AVATAR

        self.mp4_list = mp4_list
        self.gif_list = gif_list
        self.cmd_table = cmd_table

        # Client
        self.TWITTER_CLI = TWITTER_CLI
        self.DISCORD_TOKEN = DISCORD_TOKEN
        self.DISCORD_CLI = DISCORD_CLI


def init():
    log_format = "%(asctime)s [%(levelname)s]: %(message)s"
    logging.basicConfig(
        format=log_format,
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_NAME, mode="w"),
            RotatingFileHandler(LOG_NAME, maxBytes=5 * 1024, backupCount=2),
        ],
    )
    LOGGER = logging.getLogger(__name__)

    load_dotenv()

    BOT_NAME = os.environ.get("BOT_NAME")
    WEBHOOK_NAME = os.environ.get("WEBHOOK_NAME")
    fp = open(AVATAR_IMG, "rb")
    WEBHOOK_AVATAR = fp.read()
    TWITTER_CLI = twitter_client.TwitterClient()

    DISCORD_TOKEN = os.environ.get("DISCORD_CLIENT_TOKEN")

    GLOBAL_SETTINGS = GLOBAL(
        LOGGER=LOGGER,
        BOT_NAME=BOT_NAME,
        WEBHOOK_NAME=WEBHOOK_NAME,
        WEBHOOK_AVATAR=WEBHOOK_AVATAR,
        mp4_list=mp4_list,
        gif_list=gif_list,
        cmd_table=cmd_table,
        TWITTER_CLI=TWITTER_CLI,
        DISCORD_TOKEN=DISCORD_TOKEN,
    )

    DISCORD_CLI = discord_client.DiscordClient(GLOBAL_SETTINGS)

    return GLOBAL_SETTINGS, DISCORD_CLI
