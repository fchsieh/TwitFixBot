from urllib.parse import urlparse


def is_twitter_url(url):
    # make sure it's a tweet
    return all(["twitter.com" in url, "status" in url])


def is_exhentai_url(url):
    # make sure it's a gallery
    return all([("exhentai.org" in url or "e-hentai.org" in url), "/g/" in url])


def is_kemono_url(url):
    # make sure it's a gallery
    return all(["kemono.party" in url, "/post/" in url])


def build_url(url, type):
    if type == "twitter":
        return f"https://twitter.com/{urlparse(url).path[1:]}"
    elif type == "exhentai":
        return f"https://exhentai.org/{urlparse(url).path[1:]}"
    elif type == "kemono":
        return f"https://kemono.party/{urlparse(url).path[1:]}"
