import asyncio
import random
from urllib.parse import urlparse

import discord
import requests
from discord_webhook import DiscordWebhook
from twitter_lib.twitter_client import *

from discord_lib.discord_message import *

REQUEST_SUCCESS_CODE = {200, 204}
re_status = re.compile("\\w{1,15}\\/(status|statuses)\\/\\d{2,20}")


class DiscordClient(discord.Client):
    def __init__(self, GLOBAL):
        super().__init__()
        self.LOGGER = GLOBAL.LOGGER
        self.BOT_NAME = GLOBAL.BOT_NAME
        self.WEBHOOK_NAME = GLOBAL.WEBHOOK_NAME
        self.WEBHOOK_AVATAR = GLOBAL.WEBHOOK_AVATAR
        # This is used for changing webhook avatar when posting
        self.WEBHOOK_AVATAR_URL = None
        self.cmd_table = GLOBAL.cmd_table
        self.gif_list = GLOBAL.gif_list
        self.mp4_list = GLOBAL.mp4_list

        self.TWITTER_CLI = GLOBAL.TWITTER_CLI

    async def on_ready(self):
        self.LOGGER.info("Logged on as {0}!".format(self.user))
        await self.change_presence(activity=discord.Game(self.WEBHOOK_NAME))

    async def get_webhook(self, message):
        channel_all_webhooks = await message.channel.webhooks()
        send_webhook = None  # this is used for getting webhook url (for later usage)
        if len(channel_all_webhooks) == 0:
            # create webhook for twitter-fix bot
            send_webhook = await message.channel.create_webhook(
                name=self.BOT_NAME, avatar=self.WEBHOOK_AVATAR
            )
        else:
            send_webhook = discord.utils.get(channel_all_webhooks, name=self.BOT_NAME)
            if send_webhook is None:
                # need to create a new webhook for this app
                send_webhook = await message.channel.create_webhook(
                    name=self.BOT_NAME, avatar=self.WEBHOOK_AVATAR
                )

        webhook_url = send_webhook.url
        if send_webhook is None or webhook_url is None:
            self.LOGGER.error("Failed to fetch webhook")
            return

        author = message.author
        author_avatar = str(author.avatar_url)
        author_display_name = author.display_name
        webhook = DiscordWebhook(
            url=webhook_url,
            rate_limit_retry=True,
            username=author_display_name,
            avatar_url=author_avatar if author_avatar else self.WEBHOOK_AVATAR_URL,
        )

        return webhook

    async def print_help(self, channel):
        help_msg = discord.Embed(title="DM me with command! #help", color=0xFFB8D1)
        for cmd_name, cmd_desc in self.cmd_table.items():
            help_msg.add_field(name="#%s" % cmd_name, value=cmd_desc, inline=False)

        display_thumb = self.gif_list[random.randint(0, len(self.gif_list) - 1)]
        help_msg.set_thumbnail(url=display_thumb)
        await channel.send(embed=help_msg)

    async def fun(self, channel):
        await channel.send(self.mp4_list[random.randint(0, len(self.gif_list) - 1)])

    async def handle_dm_message(self, message):
        msg_list = message.content.split()
        if msg_list[0].startswith("#"):
            cmd = msg_list[0][1:]
            if cmd == "help":
                await self.print_help(message.channel)
            elif cmd == "set_avatar":
                self.LOGGER.info(
                    "User {} changed webhook avatar to {}.".format(
                        message.author, msg_list[1]
                    )
                )
                self.WEBHOOK_AVATAR_URL = msg_list[1]
                await message.channel.send(
                    "> Changed webhook avatar to <%s>" % self.WEBHOOK_AVATAR_URL
                )
            elif cmd == "set_name":
                self.LOGGER.info(
                    "User {} changed webhook name from {} to {}".format(
                        message.author, self.WEBHOOK_NAME, msg_list[1]
                    )
                )
                self.WEBHOOK_NAME = msg_list[1]
                await message.channel.send(
                    "> Changed webhook name to " + self.WEBHOOK_NAME
                )
                # Change now playing
                await self.change_presence(activity=discord.Game(self.WEBHOOK_NAME))
            elif cmd == "get_avatar":
                if self.WEBHOOK_AVATAR_URL:
                    await message.channel.send(
                        "> Current webhook avatar is " + self.WEBHOOK_AVATAR_URL
                    )
                else:
                    await message.channel.send(
                        "> Current webhook avatar is default image"
                    )
            elif cmd == "get_name":
                if self.WEBHOOK_NAME:
                    await message.channel.send(
                        "> Current webhook name is " + self.WEBHOOK_NAME
                    )
                else:
                    # using default webhook name
                    await message.channel.send(
                        "> Current webhook name is " + self.BOT_NAME
                    )
            else:
                await self.fun(message.channel)

        else:
            await self.print_help(message.channel)

    async def on_message(self, message):
        # check if user sends a message
        if message.author.bot or message.author == self.user:
            return

        # Check if this is a dm message
        if not message.guild:
            await self.handle_dm_message(message)
            return

        # Check if user mentions this bot
        if self.user in message.mentions:
            await self.fun(message.channel)
            return

        message_list = message.content.split()
        if message.content.startswith("||") and message.content.endswith("||"):
            # this is a spoiler message, skip
            self.LOGGER.info("Spoiler message, skipping")
            return

        normal_message = []
        msg_should_del = False
        for msg in message_list:
            valid_url = self.is_valid_url(msg)
            if valid_url is not None and valid_url["Twitter"]:
                # A valid tweet found, should delete the original message
                if not msg_should_del:
                    msg_should_del = True
                await self.handle_twitter_message(
                    valid_url["Twitter"], message, normal_message
                )
            else:
                # Not a valid twitter url, skipping
                normal_message.append(msg)
                continue
        # Other messages that was deleted by the bot, but should be displayed
        if msg_should_del:
            await message.delete()
            for msg in normal_message:
                await self.handle_normal_message(message, msg)

    async def handle_normal_message(self, message, normal_message):
        webhook = await self.get_webhook(message)
        if webhook is None:
            return

        webhook.set_content(normal_message)
        wh = webhook.execute()
        if wh.status_code not in REQUEST_SUCCESS_CODE:
            self.LOGGER.warning("Failed to sent message webhook!")
        else:
            self.LOGGER.info("Successfully sent message to channel")

    async def handle_twitter_message(self, is_tweet, message, normal_message):
        # Valid tweet found
        twitter_url = is_tweet
        self.LOGGER.info("Tweet Found: {}".format(twitter_url))
        # Try to fetch tweet object
        tweet = Tweet(
            url=twitter_url,
            TwitterCli=self.TWITTER_CLI,
            LOGGER=self.LOGGER,
            message=message,
        )
        if tweet is not None:  # A valid tweet found!
            is_hidden = tweet.is_hidden()
            if tweet.type == "Image":
                if not is_hidden:
                    self.LOGGER.info(
                        "This image is not hidden... Adding to normal message list"
                    )
                    # no need to post this image
                    normal_message.append(tweet.url)
                    return
                self.LOGGER.info("Hidden image found... Start processing")
                tweet.download_image()

            elif tweet.type == "Video":
                if not is_hidden:
                    self.LOGGER.info(
                        "This video/gif is not hidden... Adding to normal message list"
                    )
                    # no need to post this video/gif
                    normal_message.append(tweet.url)
                    return
                self.LOGGER.info("Hidden video/gif found... Start processing")
                tweet.download_video()

            elif tweet.type == "Text":
                self.LOGGER.info("Text tweet found... Adding to normal message list")
                normal_message.append(tweet.url)
                return  # Text tweet, save in normal message list

            else:
                self.LOGGER.warning(
                    "Failed to process, not a valid tweet? Adding to normal message list"
                )
                normal_message.append(tweet.url)
                return  # Other types of tweet

            # Build tweet info (author, date, url...)
            tweet.fetch_info()
            # get webhook to post this tweet
            webhook = await self.get_webhook(message)
            # post url first
            webhook.set_content(tweet.url)

            tweet_output = tweet.output()

            # add content to webhook message
            message_content = DiscordMessage(tweet_output, logger=self.LOGGER)
            if tweet.type == "Image":
                embed_list = message_content.embed_list
                for embed in embed_list:
                    webhook.add_embed(embed)

            elif tweet.type == "Video":
                video = message_content.video
                tweet_info = message_content.embed_list[0]
                # Send tweet info first
                webhook.add_embed(tweet_info)
                info_wh = webhook.execute()
                webhook.remove_embeds()
                if info_wh.status_code not in REQUEST_SUCCESS_CODE:
                    self.LOGGER.warning("Failed to sent video tweet info!")

                # Add video url to content, which will be sent later
                webhook.set_content(video["url"])

            # send message to this channel!
            sent_webhook = webhook.execute()
            # check status code
            if sent_webhook.status_code not in REQUEST_SUCCESS_CODE:
                self.LOGGER.warning("Failed to sent message webhook!")
            else:
                self.LOGGER.info("Successfully sent message to channel")

        else:
            # Not a valid tweet, append to normal message list
            self.LOGGER.warning("Not a valid tweet, skipping")
            normal_message.append(tweet.url)
            return

    def is_valid_url(self, url):
        # Return valid url or None if url is not valid
        parsed_url = urlparse(url)
        if not parsed_url.scheme or parsed_url.scheme not in {"http", "https"}:
            return None

        hostname = parsed_url.hostname
        if hostname == "twitter.com":
            return {"Twitter": self.is_valid_twitter_url(url)}

    def is_valid_twitter_url(self, url):
        if "twitter.com" not in url:
            # Not a valid url, skipping
            return None

        match = re_status.search(url)
        if match is not None:
            twitter_url = url
            if match.start() == 0:
                twitter_url = "https://twitter.com/" + url
            status_code = requests.get(twitter_url)
            if status_code not in REQUEST_SUCCESS_CODE:
                return twitter_url
            else:
                return None
        return None
