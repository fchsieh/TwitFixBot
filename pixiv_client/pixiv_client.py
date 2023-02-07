import logging
import os
from collections import defaultdict

from gallery_dl import config
from gppt import GetPixivToken

from packages.download import GalleryDL


class PixivClient:
    def __init__(self):
        self.log = logging.getLogger("discord")

    def _get_pixiv_token(self) -> str:
        gpt = GetPixivToken()
        res = gpt.login(
            headless=True,
            username=os.environ.get("PIXIV_USERNAME"),
            password=os.environ.get("PIXIV_PASSWORD"),
        )
        if res:
            return res["refresh_token"]
        self.log.error("Failed to get Pixiv token")
        return None

    def _set_token(self):
        token = self._get_pixiv_token()
        if token:
            # update config
            config.set(path=["extractor", "pixiv"], key="refresh-token", value=token)
            self.log.info("Pixiv token updated")
        else:
            self.log.error("Failed to set Pixiv token")

    def build(self, url) -> dict:
        j = GalleryDL(url)
        j.run()

        # check if token has expired
        auth_error = not isinstance(j.data[0][1], dict)
        if auth_error:
            self._set_token()
            j = GalleryDL(url)
            j.run()
            err = not isinstance(j.data[0][1], dict)
            if err:
                self.log.error("Failed to refresh Pixiv token")
                return None

        pixiv_metadata = j.data[0][1]
        pixiv_data = defaultdict(lambda: None)

        # Skip if post is not hidden
        rating = pixiv_metadata.get("rating", "")
        if "R-18" not in rating:
            return None

        # Set post url
        pixiv_data["post_url"] = url

        # Set images at most 4
        pixiv_data["images"] = []
        for f in j.data[1:]:
            if len(pixiv_data["images"]) > 4:
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
            # replace piximg with reverse proxy
            img_url = f[1].replace("i.pximg.net", "i.pixiv.nl")
            pixiv_data["images"].append(img_url)

        # Set date
        pixiv_data["date"] = pixiv_metadata.get("date", None)

        return pixiv_data
