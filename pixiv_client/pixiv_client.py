import logging
import os
from collections import defaultdict
from datetime import datetime

import requests


class PixivClient:
    def __init__(self):
        self.log = logging.getLogger("discord")
        self.pixiv_proxy = os.environ.get("PIXIV_PROXY")

    def _get_metadata(self, illust_id: str) -> dict:
        self.log.info(f"Getting metadata for Pixiv post {illust_id}")
        pixiv_api = f"{self.pixiv_proxy}/api/{illust_id}"
        res = requests.get(pixiv_api)
        if res.status_code not in {200, 201}:
            self.log.error(f"Failed to get metadata from {pixiv_api}")
            return None

        metadata = res.json()
        if metadata.get("error"):
            self.log.error(f"Failed to get metadata from {pixiv_api}")
            return None

        return metadata["body"]

    def build(self, url) -> dict:
        post_metadata = self._get_metadata(url.split("/")[-1])

        file_count = post_metadata["pageCount"]

        post_data = defaultdict(lambda: None)

        # Check if post is not image
        if post_metadata["illustType"] != 0:
            return None

        # Check if post is nsfw
        if post_metadata["xRestrict"] != 1:
            return None  # ignore non-nsfw posts

        # Set post url
        post_data["post_url"] = url

        # Set title
        post_data["title"] = post_metadata["title"]

        # Set images
        image_base = post_metadata["userIllusts"][post_metadata["id"]]["url"].split(
            "img-master"
        )[1]
        image_base = image_base.replace("square1200", "master1200")

        post_data["images"] = []
        for img in range(min(4, file_count)):
            cur_img = image_base.replace("_p0", f"_p{img}")
            post_data["images"].append(f"{self.pixiv_proxy}/img-master{cur_img}")

        # Set date
        post_data["date"] = datetime.fromisoformat(post_metadata["createDate"])

        return post_data
