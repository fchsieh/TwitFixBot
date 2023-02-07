import logging
import os
import re

import discord

from discord_client import discord_webhook
from exhentai_client import exhentai_client
from exhentai_client.exhentai_message import ExHentaiMessage
from packages import url_parser
from twitter_client import twitter_client
from twitter_client.twitter_message import TwitterMessage
from kemono_client import kemono_client
from kemono_client.kemono_message import KemonoMessage
from pixiv_client import pixiv_client
from pixiv_client.pixiv_message import PixivMessage

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

from packages import config


class DiscordClient(discord.Client):
    def __init__(self, intents=intents):
        super().__init__(intents=intents)
        self.log = logging.getLogger("discord")
        # Discord webhook client
        self.WebhookClient = discord_webhook.DiscordWebhook()
        # Other clients
        self.TwitterClient = twitter_client.TwitterClient()
        self.ExHentaiClient = exhentai_client.ExHentaiClient()
        self.KemonoClient = kemono_client.KemonoClient()
        self.PixivClient = pixiv_client.PixivClient()

    async def on_ready(self):
        self.log.info(f"Logged in as {self.user}")
        # Set status
        await self.change_presence(
            activity=discord.Game(name=os.environ.get("BOT_NAME"))
        )

    async def on_message(self, message: discord.Message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.author.bot:  # ignore bot's messages
            return

        if re.search(config.REGEX_URL, message.content):
            await self.on_url(message)

    async def on_url(self, message: discord.Message):
        parsed_urls = set()
        urls = [
            x.group(0)
            for x in re.finditer(config.REGEX_URL, message.content, re.IGNORECASE)
        ]
        has_twitter_url = any(url_parser.is_twitter_url(url) for url in urls)
        if has_twitter_url:
            await message.delete()

        for idx in range(len(urls)):
            url = urls[idx]
            if url_parser.is_twitter_url(url):
                await self._handle_url(
                    message,
                    message.content,
                    url,
                    parsed_urls,
                    idx == 0,
                    has_twitter_url,
                    "twitter",
                    self.TwitterClient,
                    TwitterMessage,
                )
            elif url_parser.is_exhentai_url(url):
                await self._handle_url(
                    message,
                    message.content,
                    url,
                    parsed_urls,
                    idx == 0,
                    has_twitter_url,
                    "exhentai",
                    self.ExHentaiClient,
                    ExHentaiMessage,
                )
            elif url_parser.is_kemono_url(url):
                await self._handle_url(
                    message,
                    message.content,
                    url,
                    parsed_urls,
                    idx == 0,
                    has_twitter_url,
                    "kemono",
                    self.KemonoClient,
                    KemonoMessage,
                )
            elif url_parser.is_pixiv_url(url):
                await self._handle_url(
                    message,
                    message.content,
                    url,
                    parsed_urls,
                    idx == 0,
                    has_twitter_url,
                    "pixiv",
                    self.PixivClient,
                    PixivMessage,
                )

    async def _handle_url(
        self,
        message: discord.Message,
        content: str,
        url: str,
        parsed_urls: set,
        send_orig_msg: bool,
        has_twitter_url: bool,
        type: str,
        client: object,
        message_class: object,
    ):
        # Start processing url
        url = url_parser.build_url(url, type)
        # don't send duplicate tweets
        if url in parsed_urls:
            return
        parsed_urls.add(url)
        # Build message
        content_data = client.build(url)
        if not content_data:
            self.log.info(f"Failed to build {type} message: '{url}'")
            return
        to_send = message_class(content_data, content)
        # Send to discord channel
        if to_send.build_message():
            self.log.info(f"Sending {type}: '{url}'")
            await self.WebhookClient.execute_webhook(
                original_message=content
                if send_orig_msg and has_twitter_url
                else "",  # only send original message once
                message=message,
                channel=message.channel,
                embeds=to_send.embeds,
            )
