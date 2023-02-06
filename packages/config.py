import datetime
import json
import logging
import os

from gallery_dl import config
from rich.logging import RichHandler

SERVER_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
TIMEZONE_OFFSET = (
    datetime.datetime.now(datetime.timezone.utc)
    .astimezone()
    .utcoffset()
    .total_seconds()
    / 3600
)

REGEX_URL = r"""https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"""

EXHENTAI_ICON = "https://ehwiki.org/images/c/cd/E-Hentai.png"


def log_init():
    logging.basicConfig(
        handlers=[RichHandler(rich_tracebacks=True)],
        level=logging.INFO,
        datefmt="%x %X",
        format="%(message)s",
    )


def twitter_init(config_data):
    if config_data["extractor"]["twitter"]["username"] != os.environ.get(
        "TWITTER_USERNAME"
    ):
        config_data["extractor"]["twitter"]["username"] = os.environ.get(
            "TWITTER_USERNAME"
        )
        config_data["extractor"]["twitter"]["password"] = os.environ.get(
            "TWITTER_PASSWORD"
        )
        json.dump(
            config_data,
            open(os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"), "w"),
        )


def exhentai_init(config_data):
    if config_data["extractor"]["exhentai"]["username"] != os.environ.get(
        "EXHENTAI_USERNAME"
    ):
        config_data["extractor"]["exhentai"]["username"] = os.environ.get(
            "EXHENTAI_USERNAME"
        )
        config_data["extractor"]["exhentai"]["password"] = os.environ.get(
            "EXHENTAI_PASSWORD"
        )
        json.dump(
            config_data,
            open(os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"), "w"),
        )


def init():
    config_data = json.load(
        open(os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"))
    )

    # init logging handler
    log_init()

    # init Twitter settings
    twitter_init(config_data)

    # init ExHentai settings
    exhentai_init(config_data)

    # load config
    config.load((os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"),))
