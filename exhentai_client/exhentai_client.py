import logging
from collections import defaultdict

from packages.download import GalleryDL


class ExHentaiClient:
    def __init__(self):
        self.log = logging.getLogger("discord")

    def build(self, url) -> dict:
        j = GalleryDL(url)
        j.run()

        doujin_metadata = j.data[0][1]
        first_page = j.data[1][1]
        doujin_data = defaultdict(lambda: None)

        # Set doujin url
        doujin_data["doujin_url"] = url

        # Set first page
        doujin_data["first_page"] = first_page

        # Get author
        author_candidates = [
            x
            for x in doujin_metadata.get("tags", [])
            if x.startswith("artist:") or x.startswith("group:")
        ]
        author_candidates = sorted(author_candidates)  # artist: before group:
        is_group = False
        if len(author_candidates) > 0:
            if author_candidates[0].startswith("artist:"):
                doujin_data["author"] = author_candidates[0].split("artist:")[1].title()
            else:
                is_group = True
                doujin_data["author"] = author_candidates[0].split("group:")[1].title()
        else:
            doujin_data["author"] = "Unknown"
        doujin_data["author_url"] = (
            ""
            if doujin_data["author"] == "Unknown"
            else "https://exhentai.org/tag/{}:{}".format(
                "group" if is_group else "artist", doujin_data["author"]
            ).replace(" ", "+")
        )
        doujin_data["thumb"] = first_page

        # Get title
        doujin_data["title"] = doujin_metadata.get("title", "Unknown")
        doujin_data["title_jpn"] = doujin_metadata.get("title_jpn", None)

        # Get rating and favorites
        doujin_data["rating"] = doujin_metadata.get("rating", 0)
        doujin_data["favorites"] = doujin_metadata.get("favorites", 0)

        # Get date
        doujin_data["date"] = doujin_metadata.get("date", None)

        return doujin_data
