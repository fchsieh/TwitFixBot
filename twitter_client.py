import os
import requests
import twitter
import youtube_dl
import json
from datetime import datetime
import re


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
        self.CUTTLY_API = os.environ.get("CUTTLY_API")


class Tweet:
    def __init__(self, url=None, TwitterCli=None):
        self.url = url
        self.tweet = None  # tweet object from twitter api
        self.type = None  # tweet type: Image, Video, Text
        self.content = {}  # content that will be passed to DiscordMessage
        self.TwitterCli = TwitterCli
        self.process_tweet()

    def is_hidden(self):
        if self.tweet["possibly_sensitive"] is not None:
            return self.tweet["possibly_sensitive"]
        else:
            return False

    def process_tweet(self):
        twid = int(re.sub(r"\?.*$", "", self.url.rsplit("/", 1)[-1]))
        try:
            self.tweet = self.TwitterCli.twitter_api.statuses.show(
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
        self.content["Type"] = self.type
        self.content["Tweet_url"] = self.url

    def download_image(self):
        if self.type != "Image" or self.tweet is None:
            return
        imgs = ["", "", "", "", ""]
        i = 0
        for media in self.tweet["extended_entities"]["media"]:
            imgs[i] = media["media_url_https"]
            i += 1

        imgs[4] = i
        images = imgs
        self.content["Images"] = images

    def download_video(self, method="youtube-dl"):
        if self.type != "Video" or self.tweet is None:
            return
        vid_url = None

        if method == "youtube-dl":
            # use youtube_dl method
            with youtube_dl.YoutubeDL({"outtmpl": "%(id)s.%(ext)s"}) as ydl:
                result = ydl.extract_info(self.url, download=False)
                self.content["Video_url"] = result["url"]
                self.content["Thumbnail"] = result["thumbnail"]

        elif method == "api":
            if self.tweet["extended_entities"]["media"][0]["video_info"]["variants"]:
                best_bitrate = 0
                thumb = self.tweet["extended_entities"]["media"][0]["media_url"]
                for video in self.tweet["extended_entities"]["media"][0]["video_info"][
                    "variants"
                ]:
                    if (
                        video["content_type"] == "video/mp4"
                        and video["bitrate"] > best_bitrate
                    ):
                        vid_url = video["url"]
                        best_bitrate = video["bitrate"]
                self.content["Video_url"] = vid_url
                self.content["Thumbnail"] = thumb

        # shorten video url
        url = self.content["Video_url"]
        short_url = requests.get(
            "http://cutt.ly/api/api.php?key={}&short={}".format(
                self.TwitterCli.CUTTLY_API, url
            )
        )
        short_url = json.loads(short_url.text)
        if short_url and short_url["url"]:
            self.content["Video_url"] = short_url["url"]["shortLink"]
        # failed to shorten url, using original url instead

    def output(self):
        return self.content
