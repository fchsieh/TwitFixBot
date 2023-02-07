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
            post_data["images"].append(f[1])

        # Set date
        post_data["date"] = post_metadata.get("date", None)

        # Check if file count matches image count
        if file_count <= 4 and file_count != len(post_data["images"]):
            self.log.warning(
                f"File count and media count do not match, file count : {file_count} media count: {len(post_data['images'])}"
            )

        return post_data
