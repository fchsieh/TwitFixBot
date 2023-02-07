import logging
from collections import defaultdict

from packages.download import GalleryDL


class KemonoClient:
    def __init__(self):
        self.log = logging.getLogger("discord")

    def build(self, url) -> dict:
        j = GalleryDL(url)
        j.run()

        post_metadata = j.data[0][1]
        post_data = defaultdict(lambda: None)

        # Set post url
        post_data["post_url"] = url

        # Get file count
        file_count = post_metadata.get("count", 0)

        # Set images at most 4
        post_data["images"] = []
        for f in j.data[1:]:
            if len(post_data["images"]) > 4:
                break
            # ignore if file is not an image
            if f[1].split(".")[-1] not in {
                "jpg",
                "png",
                "jpeg",
                "gif",
                "jfif",
                "webp",
                "tiff",
                "bmp",
            }:
                continue
            post_data["images"].append(f[1])

        # Set date
        post_data["date"] = post_metadata.get("date", None)

        return post_data
