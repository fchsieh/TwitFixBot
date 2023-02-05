import json
import logging
import os

from gallery_dl import config
from rich.logging import RichHandler


def log_init():
    logging.basicConfig(
        handlers=[RichHandler(rich_tracebacks=True)],
        level=logging.INFO,
        datefmt="%x %X",
        format="%(message)s"
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

    config.load((os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"),))


def init():
    config_data = json.load(
        open(os.path.join(os.path.dirname(__file__), "..", "gallery-dl.json"))
    )

    # init logging handler
    log_init()

    # init Twitter settings
    twitter_init(config_data)
