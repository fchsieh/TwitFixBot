import logging
from datetime import timedelta

from discord_webhook import DiscordEmbed

from packages import config


class ExHentaiMessage:
    def __init__(self, content_dict: dict, original_message: str):
        self.log = logging.getLogger("discord")
        self.content_dict = content_dict
        self.original_message = original_message
        self.embeds = []

    def exhentai_base_embed(self) -> DiscordEmbed:
        if not all(
            [
                self.content_dict["doujin_url"],
                self.content_dict["first_page"],
                self.content_dict["title"],
                self.content_dict["date"],
            ]
        ):
            self.log.warning("Not all required fields are present")
            return None

        embed = DiscordEmbed(url=self.content_dict["doujin_url"])
        embed.set_color(0x660611)

        # Set author
        embed.set_author(
            name=self.content_dict["author"],
            url=self.content_dict["author_url"],
            icon_url=config.EXHENTAI_ICON,
        )
        # Set title
        embed.set_title(title=self.content_dict["title"])

        # Set subtitle
        embed.set_description(self.content_dict["title_jpn"])

        # Set image
        embed.set_image(url=self.content_dict["first_page"])

        # Set rating and favorites
        embed.add_embed_field(
            name="Rating", value=self.content_dict["rating"], inline=True
        )
        embed.add_embed_field(
            name="Favorites", value=self.content_dict["favorites"], inline=True
        )

        # Set footer
        embed.set_footer(text="ExHentai.org")

        # Set timestamp
        shifted_date = self.content_dict["date"] + timedelta(
            hours=config.TIMEZONE_OFFSET
        )
        embed.set_timestamp(shifted_date.timestamp())

        return embed

    def build_message(self) -> bool:
        self.embeds = [self.exhentai_base_embed()]
        if not self.embeds:
            self.log.warning("ExHentai: No embeds were created")
            return False
        return True
