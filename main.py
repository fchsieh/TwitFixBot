import os
import re
import json
from datetime import datetime

import discord
import requests
import twitter
from dotenv import load_dotenv

re_status = re.compile("\\w{1,15}\\/(status|statuses)\\/\\d{2,20}")

# set twitter api
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
        return self.tweet["possibly_sensitive"]

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
        self.content["Description"] = self.tweet["full_text"]
        self.content["Likes"] = self.tweet["favorite_count"]
        self.content["Retweets"] = self.tweet["retweet_count"]
        created_at = datetime.strptime(
            self.tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y"
        )
        self.content["Time"] = created_at.strftime("%Y/%m/%d")

    def download_image(self):
        if self.type != "Image" or self.tweet is None:
            return
        imgs = ["", "", "", "", ""]
        i = 0
        for media in self.tweet["extended_entities"]["media"]:
            imgs[i] = media["media_url_https"]
            i = i + 1

        # print(imgs)
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
        self.main_content = None
        self.build_message()

    def build_message(self):
        type = self.content["Type"]
        message_content = {
            "embeds": [],
        }

        if type == "Image":
            image_count = self.content["Images"][-1]
            image_list = self.content["Images"][:image_count]

            for image in range(image_count):
                image_content = {"type": "rich", "url": self.content["Tweet_url"]}
                if image == 0:
                    # set tweet info
                    image_content["author"] = {
                        "name": self.content["Author"],
                        "url": self.content["Author_url"],
                        "icon_url": self.content["Author_icon_img"],
                    }
                    image_content["fields"] = [
                        {
                            "name": "Likes",
                            "value": self.content["Likes"],
                            "inline": "true",
                        },
                        {
                            "name": "Retweets",
                            "value": self.content["Retweets"],
                            "inline": "true",
                        },
                    ]
                    image_content["color"] = 0x3498DB
                    image_content["description"] = self.content["Description"]
                    image_content["footer"] = {
                        "text": "Twitter  |  {}".format(self.content["Time"]),
                        "icon_url": "https://cdn.cms-twdigitalassets.com/content/dam/developer-twitter/images/Twitter_logo_blue_16.png",
                    }

                image_content["image"] = {"url": image_list[image]}
                message_content["embeds"].append(image_content)

        self.main_content = json.loads(json.dumps(message_content))


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def get_webhook(self, message):
        ch_webhooks = await message.channel.webhooks()
        webhook = None
        if len(ch_webhooks) == 0:
            # create webhook for twitter-fix bot
            fp = open("./avatar.jpeg", "rb")
            webhook = await message.channel.create_webhook(
                name="rinchan", avatar=fp.read()
            )
        else:
            webhook = discord.utils.get(ch_webhooks, name="twitter-fix")
            if webhook is None:
                # need to create a new webhook for this app
                fp = open("./avatar.jpeg", "rb")
                webhook = await message.channel.create_webhook(
                    name="rinchan", avatar=fp.read()
                )

        webhook_url = webhook.url
        if webhook_url is None:
            raise Exception("Failed to fetch webhook")

        return webhook_url

    async def on_message(self, message):
        # check if user sends a twitter url
        if message.author.bot:
            return

        message_list = message.content.split()
        if message_list[0].startswith("||") and message_list[-1].endswith("||"):
            # this is a spoiler message, skip
            return

        for msg in message_list:
            is_tweet = self.is_valid_twitter_url(msg)
            if is_tweet is not None:
                twitter_url = is_tweet
                print("> Tweet Found: %s" % twitter_url)
                # Try to fetch tweet object
                tweet = Tweet(twitter_url)
                if tweet is not None:  # A valid message found!
                    if tweet.type == "Image":
                        if not tweet.is_hidden():
                            # no need to post this image
                            continue
                        print(">> Hidden image found, start posting")
                        tweet.download_image()
                    elif tweet.type == "Video":
                        continue  # not implemented yet
                    elif tweet.type == "Text":
                        continue  # not implemented yet
                    else:
                        print("Error, not a valid tweet?")
                        continue  # not implemented yet

                    # Build tweet info (author, date, url...)
                    tweet.fetch_info()
                    # get webhook to post this tweet
                    webhook = await self.get_webhook(message)

                    tweet_output = tweet.output()
                    main_content = DiscordMessage(tweet_output).main_content
                    # send message to this channel!
                    post_res = requests.post(
                        webhook,
                        json=main_content,
                    )
                    if post_res.status_code == 400:
                        print("Failed to post to the webhook!")
                else:
                    print("Failed to fetch this tweet!")
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
    load_dotenv()
    TwitterAPI = TwitterClient()
    TOKEN = os.environ.get("CLIENT_TOKEN")
    client = MyClient()
    client.run(TOKEN)
