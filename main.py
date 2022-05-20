import asyncio
import logging
import os
import re
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import discord
import requests
import twitter
from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv

re_status = re.compile("\\w{1,15}\\/(status|statuses)\\/\\d{2,20}")

# Set bot info
WEBHOOK_NAME = ""
AVATAR_IMG = "./avatar.jpeg"
BOT_AVATAR = None
LOG_NAME = "twitfix.log"
# Set twitter api
TwitterAPI = None


class TwitterClient:
    def __init__(self):
        _access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        _access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
        _api_key = os.environ.get("TWITTER_API_KEY")
        _api_secret = os.environ.get("TWITTER_API_SECRET")

        _auth = twitter.oauth.OAuth(
            _access_token,
            _access_token_secret,
            _api_key,
            _api_secret,
        )
        self.twitter_api = twitter.Twitter(auth=_auth)


class Tweet:
    def __init__(self, url=None):
        self.url = url
        self.tweet = None  # tweet object from twitter api
        self.type = None  # tweet type: Image, Video, Text
        self.content = {}  # content that will be passed to DiscordMessage
        self.process_tweet()

    def is_hidden(self):
        if self.tweet["possibly_sensitive"] is not None:
            return self.tweet["possibly_sensitive"]
        else:
            return False

    def process_tweet(self):
        twid = int(re.sub(r"\?.*$", "", self.url.rsplit("/", 1)[-1]))
        try:
            self.tweet = TwitterAPI.twitter_api.statuses.show(
                _id=twid, tweet_mode="extended"
            )
        except:
            # not a valid tweet
            self.tweet = None

        if self.tweet is not None:
            self.tweet_type()

    def tweet_type(self):
        if "extended_entities" in self.tweet:
            if "video_info" in self.tweet["extended_entities"]["media"][0]:
                self.type = "Video"
            else:
                self.type = "Image"
        else:
            self.type = "Text"

    def fetch_info(self):
        screen_name = self.tweet["user"]["screen_name"]
        self.content["Author"] = "{} (@{})".format(
            self.tweet["user"]["name"], screen_name
        )
        self.content["Author_url"] = "https://twitter.com/{}".format(screen_name)
        self.content["Author_icon_img"] = self.tweet["user"]["profile_image_url_https"]
        if "full_text" not in self.tweet:
            self.content["Description"] = self.tweet["text"]  # Not sure about this
        else:
            self.content["Description"] = self.tweet["full_text"].rsplit(" ", 1)[0]
        self.content["Likes"] = self.tweet["favorite_count"]
        self.content["Retweets"] = self.tweet["retweet_count"]
        created_at = datetime.strptime(
            self.tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y"
        )
        self.content["Timestamp"] = created_at.timestamp()

    def download_image(self):
        if self.type != "Image" or self.tweet is None:
            return
        imgs = ["", "", "", "", ""]
        i = 0
        for media in self.tweet["extended_entities"]["media"]:
            imgs[i] = media["media_url_https"]
            i = i + 1

        imgs[4] = i
        images = imgs
        thumb = self.tweet["extended_entities"]["media"][0]["media_url_https"]
        self.content["Images"] = images
        self.content["Thumb"] = thumb
        self.content["Tweet_url"] = self.url
        self.content["Type"] = self.type

    def download_vid(self):
        if self.type != "Video":
            return
        pass

    def output(self):
        return self.content


class DiscordMessage:
    def __init__(self, content=None):
        self.content = content
        self.embed_list = []
        self.build_message()

    def build_message(self):
        type = self.content["Type"]

        if type == "Image":
            image_count = self.content["Images"][-1]
            image_list = self.content["Images"][:image_count]

            for image in range(image_count):
                embed = DiscordEmbed(url=self.content["Tweet_url"])
                if image == 0:
                    # set basic tweet info
                    embed.set_color(1942002)
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

                embed.set_image(url=image_list[image])
                self.embed_list.append(embed)


class MyClient(discord.Client):
    async def on_ready(self):
        logging.info("Logged on as {0}!".format(self.user))

    async def get_webhook(self, message):
        channel_all_webhooks = await message.channel.webhooks()
        send_webhook = None  # this is used for getting webhook url (for later usage)
        if len(channel_all_webhooks) == 0:
            # create webhook for twitter-fix bot
            send_webhook = await message.channel.create_webhook(
                name=WEBHOOK_NAME, avatar=BOT_AVATAR
            )
        else:
            send_webhook = discord.utils.get(channel_all_webhooks, name=WEBHOOK_NAME)
            if send_webhook is None:
                # need to create a new webhook for this app
                send_webhook = await message.channel.create_webhook(
                    name=WEBHOOK_NAME, avatar=BOT_AVATAR
                )

        webhook_url = send_webhook.url
        if send_webhook is None or webhook_url is None:
            logging.error("Failed to fetch webhook")
            return

        webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)

        return webhook

    async def on_message(self, message):
        # check if user sends a twitter url
        if message.author.bot:
            return

        message_list = message.content.split()
        if message_list[0].startswith("||") and message_list[-1].endswith("||"):
            # this is a spoiler message, skip
            return

        embeds_list = []
        if message.embeds:
            for embed in message.embeds:
                embeds_list.append(embed.url)  # urls that have embed, should be skipped

        for msg in message_list:
            is_tweet = self.is_valid_twitter_url(msg)
            if is_tweet is not None:
                twitter_url = is_tweet
                logging.info("Tweet Found: {}".format(twitter_url))
                # Try to fetch tweet object
                tweet = Tweet(twitter_url)
                if tweet is not None:  # A valid message found!
                    if tweet.type == "Image":
                        if not tweet.is_hidden() or tweet.url in embeds_list:
                            logging.info("This is not a hidden tweet... Skipped")
                            # no need to post this image
                            continue
                        logging.info("Hidden image found... Start processing")
                        tweet.download_image()
                    elif tweet.type == "Video":
                        continue  # not implemented yet
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
                    embed_list = DiscordMessage(tweet_output).embed_list

                    # add content to webhook message
                    for embed in embed_list:
                        webhook.add_embed(embed)

                    # send message to this channel!
                    sent_webhook = webhook.execute()
                    # check status code
                    if sent_webhook.status_code >= 400:
                        logging.warning("Failed to sent webhook!")
                    else:
                        logging.info("Successfully sent message to channel")

                    # Check if this message has embed again (if true, delete the sent webhook)
                    await asyncio.sleep(5)

                    if message.embeds:
                        embed_url_list = [embed.url for embed in message.embeds]
                        if tweet.url in embed_url_list:
                            # delete latest image from bot
                            logging.info(
                                "Deleting sent webhook, previous message has embed (should not be sent)"
                            )
                            webhook.delete(sent_webhook)

                else:
                    logging.warning("Failed to process this tweet")
                    continue

    def is_valid_twitter_url(self, url):
        if "://twitter.com" not in url:
            return None
        match = re_status.search(url)
        if match is not None:
            twitter_url = url
            if match.start() == 0:
                twitter_url = "https://twitter.com/" + url
            # try to request this url and check whether it is a valid tweet
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
    WEBHOOK_NAME = os.environ.get("WEBHOOK_NAME")

    fp = open(AVATAR_IMG, "rb")
    BOT_AVATAR = fp.read()

    TwitterAPI = TwitterClient()
    DISCORD_TOKEN = os.environ.get("DISCORD_CLIENT_TOKEN")
    client = MyClient()
    client.run(DISCORD_TOKEN)
