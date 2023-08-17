import logging
from collections import defaultdict

from packages.download import GalleryDL


class TwitterClient:
    def __init__(self):
        self.log = logging.getLogger("discord")

    def build(self, url) -> dict:
        j = GalleryDL(url)
        j.run()
        if len(j.data) == 0:
            self.log.warning("No data found, falling back to send tweet url")
            return {"tweet_url": url, "is_fallback": True}

        tweet_information = j.data[0][1]

        try:
            file_count = tweet_information["count"]
        except TypeError:
            self.log.warning(
                "No data found, falling back to send tweet url (comment section limited by author)"
            )
            return {"tweet_url": url, "is_fallback": True}

        tweet_data = defaultdict(lambda: None)

        # Set tweet url
        tweet_data["tweet_url"] = url

        # Get author data
        tweet_data["user_nick"] = tweet_information["user"]["nick"]
        tweet_data["user_name"] = tweet_information["user"]["name"]
        tweet_data["user_url"] = f"https://twitter.com/{tweet_data['user_name']}"
        tweet_data["user_image"] = tweet_information["user"]["profile_image"]

        # Get content
        tweet_data["content"] = tweet_information["content"]

        # Get likes and retweets
        tweet_data["likes"] = tweet_information["favorite_count"]
        tweet_data["retweets"] = tweet_information["retweet_count"]

        # Get post date
        tweet_data["date"] = tweet_information["date"]

        # Get media and check if tweet has video or has images
        tweet_data["is_video"] = False
        tweet_data["is_image"] = False

        tweet_data["media"] = []
        for f in j.data[1:]:
            if len(tweet_data["media"]) == file_count:
                break  # break if we have all the files
            tweet_data["media"].append(f[1])
            if "video" in f[1]:
                tweet_data["is_video"] = True
            elif "pbs" in f[1]:  # domain for images
                tweet_data["is_image"] = True

        return tweet_data
