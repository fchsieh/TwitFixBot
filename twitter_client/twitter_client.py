import logging
from collections import defaultdict

from packages.download import GalleryDL


class TwitterClient:
    def __init__(self):
        self.log = logging.getLogger("discord")

    def build_tweet(self, url) -> dict:
        j = GalleryDL(url)
        j.run()

        tweet_metadata = j.data[0][1]

        file_count = tweet_metadata["count"]
        tweet_data = defaultdict(lambda: None)

        # Set tweet url
        tweet_data["tweet_url"] = url

        # Get author data
        tweet_data["user_nick"] = tweet_metadata["user"]["nick"]
        tweet_data["user_name"] = tweet_metadata["user"]["name"]
        tweet_data["user_url"] = f"https://twitter.com/{tweet_data['user_name']}"
        tweet_data["user_image"] = tweet_metadata["user"]["profile_image"]

        # Get content
        tweet_data["content"] = tweet_metadata["content"]

        # Get likes and retweets
        tweet_data["likes"] = tweet_metadata["favorite_count"]
        tweet_data["retweets"] = tweet_metadata["retweet_count"]

        # Get post date
        tweet_data["date"] = tweet_metadata["date"]

        # Get media and check if tweet has video or has images
        tweet_data["is_video"] = False
        tweet_data["is_image"] = False

        tweet_data["media"] = []
        for f in j.data[1:]:
            tweet_data["media"].append(f[1])
            if "video" in f[1]:
                tweet_data["is_video"] = True
            elif "pbs" in f[1]:  # domain for images
                tweet_data["is_image"] = True

        if file_count != len(tweet_data["media"]):
            self.log.warning(
                f"File count and media count do not match, file count : {file_count} media count: {len(tweet_data['media'])}"
            )

        return tweet_data
