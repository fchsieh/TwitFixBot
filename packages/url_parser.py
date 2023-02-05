from urllib.parse import urlparse


def is_twitter_url(url):
    # make sure it's a tweet
    return all(["twitter.com" in url, "status" in url])


def build_url(url):
    return f"https://twitter.com/{urlparse(url).path[1:]}"
