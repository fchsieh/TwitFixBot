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
            await self.handle_url(message)

    async def handle_url(self, message: discord.Message):
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
                await self._handle_twitter_url(
                    message, message.content, url, parsed_urls, idx == 0
                )
            elif url_parser.is_exhentai_url(url):
                await self._handle_exhentai_url(
                    message,
                    message.content,
                    url,
                    parsed_urls,
                    idx == 0,
                    has_twitter_url,
                )

    async def _handle_twitter_url(
        self,
        message: discord.Message,
        content: str,
        url: str,
        parsed_urls: set,
        send_orig_msg: bool,
    ):
        # Start processing url
        twitter_url = url_parser.build_url(url, "twitter")
        # don't send duplicate tweets
        if twitter_url in parsed_urls:
            return
        parsed_urls.add(twitter_url)
        # Build tweet message
        tweet = self.TwitterClient.build_tweet(twitter_url)
        tweet_message = TwitterMessage(tweet, content)
        # Send tweet to discord channel
        if tweet_message.build_message():
            self.log.info(f"Sending tweet: '{twitter_url}'")
            await self.WebhookClient.execute_webhook(
                original_message=content
                if send_orig_msg
                else "",  # only send original message once
                message=message,
                channel=message.channel,
                embeds=tweet_message.embeds,
            )

    async def _handle_exhentai_url(
        self,
        message: discord.Message,
        content: str,
        url: str,
        parsed_urls: set,
        send_orig_msg: bool,
        has_twitter_url: bool,
    ):
        # For exhentai urls, don't delete original message

        # Start processing url
        exhentai_url = url_parser.build_url(url, "exhentai")
        # don't send duplicate doujins
        if exhentai_url in parsed_urls:
            return
        parsed_urls.add(exhentai_url)
        # Build doujin info
        doujin = self.ExHentaiClient.build_doujin(exhentai_url)
        doujin_message = ExHentaiMessage(doujin, message.content)
        # Send doujin to discord channel
        if doujin_message.build_message():
            self.log.info(f"Sending doujin: '{exhentai_url}'")
            await self.WebhookClient.execute_webhook(
                original_message=content
                if send_orig_msg and has_twitter_url
                else "",  # only send original message once
                message=message,
                channel=message.channel,
                embeds=doujin_message.embeds,
            )
