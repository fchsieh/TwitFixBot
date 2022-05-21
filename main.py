import asyncio
import logging
import os
import random
import re
from logging.handlers import RotatingFileHandler

import discord
import requests
from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv

from twitter_client import *

re_status = re.compile("\\w{1,15}\\/(status|statuses)\\/\\d{2,20}")

# Set global configuration
TWITTER_CLI = None

# Set bot info
BOT_NAME = ""
WEBHOOK_NAME = ""
AVATAR_IMG = "./avatar.jpg"  # Default image when creating webhook
WEBHOOK_AVATAR = None
WEBHOOK_AVATAR_URL = None
LOG_NAME = "twitfix.log"


class DiscordMessage:
    def __init__(self, content=None):
        self.content = content
        self.embed_list = []
        self.video = {
            "url": None,
            "thumbnail": None,
        }
        self.discord_colors = {"Twitter": 1942002}
        self.build_message()

    def twitter_embed_block(self, isBase=False):
        embed = DiscordEmbed(url=self.content["Tweet_url"])
        if isBase:
            # set basic tweet info
            embed.set_color(self.discord_colors["Twitter"])
            embed.set_description(self.content["Description"])
            embed.set_author(
                name=self.content["Author"],
                url=self.content["Author_url"],
                icon_url=self.content["Author_icon_img"],
            )
            embed.add_embed_field(
                name="Likes", value=self.content["Likes"], inline=True
            )
            embed.add_embed_field(
                name="Retweets", value=self.content["Retweets"], inline=True
            )
            embed.set_footer(
                text="Twitter",
                proxy_icon_url="https://images-ext-1.discordapp.net/external/bXJWV2Y_F3XSra_kEqIYXAAsI3m1meckfLhYuWzxIfI/https/abs.twimg.com/icons/apple-touch-icon-192x192.png",
                icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
            )
            embed.set_timestamp(timestamp=self.content["Timestamp"])
        return embed

    def build_message(self):
        type = self.content["Type"]

        if type == "Image":
            image_count = self.content["Images"][-1]
            image_list = self.content["Images"][:image_count]

            for image in range(image_count):
                if image == 0:
                    embed = self.twitter_embed_block(isBase=True)
                else:
                    embed = self.twitter_embed_block(isBase=False)

                embed.set_image(url=image_list[image])
                self.embed_list.append(embed)

        elif type == "Video":
            embed = self.twitter_embed_block(isBase=True)
            self.embed_list.append(embed)

            if self.content["Video_url"] is None:
                logging.warning("Failed to fetch video url")
            self.video["url"] = self.content["Video_url"]
            self.video["thumbnail"] = self.content["Thumbnail"]


class DiscordClient(discord.Client):
    async def on_ready(self):
        logging.info("Logged on as {0}!".format(self.user))

    async def get_webhook(self, message):
        channel_all_webhooks = await message.channel.webhooks()
        send_webhook = None  # this is used for getting webhook url (for later usage)
        if len(channel_all_webhooks) == 0:
            # create webhook for twitter-fix bot
            send_webhook = await message.channel.create_webhook(
                name=BOT_NAME, avatar=WEBHOOK_AVATAR
            )
        else:
            send_webhook = discord.utils.get(channel_all_webhooks, name=BOT_NAME)
            if send_webhook is None:
                # need to create a new webhook for this app
                send_webhook = await message.channel.create_webhook(
                    name=BOT_NAME, avatar=WEBHOOK_AVATAR
                )

        webhook_url = send_webhook.url
        if send_webhook is None or webhook_url is None:
            logging.error("Failed to fetch webhook")
            return

        webhook = DiscordWebhook(
            url=webhook_url,
            rate_limit_retry=True,
            username=WEBHOOK_NAME,
            avatar_url=WEBHOOK_AVATAR_URL if WEBHOOK_AVATAR_URL else None,
        )

        return webhook

    async def print_help(self, channel):
        help_msg = discord.Embed(title="DM me with commands")
        cmd_table = {
            "help": "Output this help message",
            "change_avatar <url_link>": "Change webhook avatar",
            "change_name <name>": "Change webhook name",
        }
        for cmd_name, cmd_desc in cmd_table.items():
            help_msg.add_field(name="#%s" % cmd_name, value=cmd_desc, inline=False)

        await channel.send(embed=help_msg)

    async def fun(self, channel):
        await self.print_help(channel)
        gif_list = [
            "https://i.imgur.com/t1Iifjr.gif",
            "https://i.imgur.com/ELiPyOi.gif",
            "https://i.imgur.com/rlNzFXZ.gif",
            "https://i.imgur.com/JvhprC9.gif",
            "https://i.imgur.com/7CjTRo7.gif",
        ]
        await channel.send(gif_list[random.randint(0, len(gif_list) - 1)])

    async def handle_dm_message(self, message):
        msg_list = message.content.split()
        if msg_list[0].startswith("#"):
            cmd = msg_list[0][1:]
            if cmd == "help":
                await self.print_help(message.channel)
            elif cmd == "change_avatar":
                global WEBHOOK_AVATAR_URL
                WEBHOOK_AVATAR_URL = msg_list[1]
                await message.channel.send(
                    "Changed webhook avatar to <%s>" % WEBHOOK_AVATAR_URL
                )
            elif cmd == "change_name":
                global WEBHOOK_NAME
                WEBHOOK_NAME = msg_list[1]
                await message.channel.send("Changed webhook name to " + WEBHOOK_NAME)
        else:
            await self.fun(message.channel)

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
            logging.info("Spoiler message, skipping")
            return

        embeds_list = []
        if message.embeds:
            for embed in message.embeds:
                embeds_list.append(embed.url)  # urls that have embed, should be skipped

        for msg in message_list:
            is_tweet = self.is_valid_twitter_url(msg)
            if is_tweet is not None:
                # Valid tweet found
                twitter_url = is_tweet
                logging.info("Tweet Found: {}".format(twitter_url))
                # Try to fetch tweet object
                tweet = Tweet(twitter_url, TWITTER_CLI)
                if tweet is not None:  # A valid message found!
                    if tweet.type == "Image":
                        if not tweet.is_hidden() or tweet.url in embeds_list:
                            logging.info("This is not a hidden tweet... Skipping")
                            # no need to post this image
                            continue
                        logging.info("Hidden image found... Start processing")
                        tweet.download_image()

                    elif tweet.type == "Video":
                        if not tweet.is_hidden():
                            logging.info("This is not a hidden tweet... Skipping")
                            # no need to post this video/gif
                            continue
                        logging.info("Hidden video/gif found... Start processing")
                        tweet.download_video(method="youtube-dl")

                    elif tweet.type == "Text":
                        continue  # not implemented yet

                    else:
                        logging.warning("Failed to process, not a valid tweet?")
                        continue  # not implemented yet

                    # Build tweet info (author, date, url...)
                    tweet.fetch_info()
                    # get webhook to post this tweet
                    webhook = await self.get_webhook(message)

                    tweet_output = tweet.output()

                    # add content to webhook message
                    message_content = DiscordMessage(tweet_output)
                    if tweet.type == "Image":
                        embed_list = message_content.embed_list
                        for embed in embed_list:
                            webhook.add_embed(embed)

                    elif tweet.type == "Video":
                        video = message_content.video
                        embed = message_content.embed_list[0]
                        webhook.add_embed(embed)
                        # send embed first
                        webhook.execute()
                        webhook.remove_embeds()
                        webhook.set_content(video["url"])

                    # send message to this channel!
                    sent_webhook = webhook.execute()
                    # check status code
                    if sent_webhook.status_code >= 400:  # Server or Client error
                        logging.warning("Failed to sent webhook!")
                    else:
                        logging.info("Successfully sent message to channel")

                    # Check if this message has embed again (if true, delete the sent webhook)
                    if tweet.type == "Image":
                        await asyncio.sleep(2)
                        if message.embeds:
                            embed_url_list = [embed.url for embed in message.embeds]
                            if tweet.url in embed_url_list:
                                # delete latest image from bot
                                logging.info(
                                    "Deleting sent webhook, previous message has embed (should not be sent)"
                                )
                                webhook.delete(sent_webhook)

                else:
                    # Not a valid tweet
                    logging.warning("Failed to process this tweet")
                    continue
            else:
                # This is not a tweet url, skipping...
                continue

    def is_valid_twitter_url(self, url):
        if "twitter.com" not in url:
            # Not a valid url, skipping
            return None

        match = re_status.search(url)
        if match is not None:
            twitter_url = url
            if match.start() == 0:
                twitter_url = "https://twitter.com/" + url
            # try to request this url and check whether it is a valid tweet
            if not url.startswith("https://twitter.com"):
                # not a valied tweet! (status found, but might not be a twitter url)
                return None
            status_code = requests.get(twitter_url)
            if status_code != 404:
                return twitter_url
            else:
                return None
        return None


if __name__ == "__main__":
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

    load_dotenv()
    # Set global variables and bot configuration
    BOT_NAME = os.environ.get("BOT_NAME")
    WEBHOOK_NAME = os.environ.get("WEBHOOK_NAME")
    fp = open(AVATAR_IMG, "rb")
    WEBHOOK_AVATAR = fp.read()
    TWITTER_CLI = TwitterClient()

    # Set discord client
    DISCORD_TOKEN = os.environ.get("DISCORD_CLIENT_TOKEN")
    DiscordCli = DiscordClient()
    DiscordCli.run(DISCORD_TOKEN)
