import logging

from discord_webhook import DiscordEmbed


class KemonoMessage:
    def __init__(self, content_dict: dict, original_message: str):
        self.log = logging.getLogger("discord")
        self.content_dict = content_dict
        self.original_message = original_message
        self.embeds = []

    def kemono_base_embed(self, is_base=False) -> DiscordEmbed:
        if len(self.content_dict["images"]) == 0:
            self.log.warning("No images found")
            return None

        embed = DiscordEmbed(url=self.content_dict["post_url"])
        if is_base:
            embed.set_color(0xE7702F)

            # Set title
            embed.set_title(title=self.content_dict["title"])

            # Set footer
            embed.set_footer(
                text="Kemono",
                proxy_icon_url="https://i.imgur.com/CKPoBpM.png",
                icon_url="https://i.imgur.com/CKPoBpM.png",
            )

            # Set timestamp  (kemono doesn't have a timezone offset)
            embed.set_timestamp(self.content_dict["date"].timestamp())

        return embed

    def build_message(self) -> bool:
        image_count = len(self.content_dict["images"])
        for img in range(image_count):
            if img == 0:
                embed = self.kemono_base_embed(is_base=True)
            else:
                embed = self.kemono_base_embed(is_base=False)
            # for multiple images, discord requires a new embed for each image
            embed.set_image(url=self.content_dict["images"][img])
            self.embeds.append(embed)

        if len(self.embeds) > 0:
            return True
        return False
