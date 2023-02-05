import logging
import re

import discord

from discord_client import discord_webhook
from packages import url_parser
from twitter_client import twitter_client
from twitter_client.twitter_message import TwitterMessage

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

REGEX_URL = r"""https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"""


class DiscordClient(discord.Client):
    def __init__(self, intents=intents):
        super().__init__(intents=intents)
        self.log = logging.getLogger("discord")

        self.WebhookClient = discord_webhook.DiscordWebhook()
        self.TwitterClient = twitter_client.TwitterClient()

    async def on_ready(self):
        self.log.info(f"Logged in as {self.user}")

    async def on_message(self, message: discord.Message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.author.bot:  # ignore bot's messages
            return

        if re.search(REGEX_URL, message.content):
            await self.handle_url(message)

    async def handle_url(self, message: discord.Message):
        parsed_urls = set()
        orig_message_deleted = False
        orig_message_sent = False
        for url in re.finditer(REGEX_URL, message.content, re.IGNORECASE):
            url = url.group(0)  # type: str
            if url_parser.is_twitter_url(url):
                # Contains twitter url, delete original message
                if not orig_message_deleted:
                    await message.delete()
                    orig_message_deleted = True

                # Start processing url
                twitter_url = url_parser.build_url(url)
                # don't send duplicate tweets
                if twitter_url in parsed_urls:
                    continue
                parsed_urls.add(twitter_url)
                # Build tweet message
                tweet = self.TwitterClient.build_tweet(twitter_url)
                tweet_message = TwitterMessage(tweet, message.content)
                # Send tweet to discord channel
                if await tweet_message.build_message():
                    self.log.info(f"Sending tweet: '{twitter_url}'")
                    await self.WebhookClient.execute_webhook(
                        original_message=message.content
                        if not orig_message_sent
                        else "",  # only send original message once
                        message=message,
                        channel=message.channel,
                        embeds=tweet_message.embeds,
                    )
                    if not orig_message_sent:
                        orig_message_sent = True
