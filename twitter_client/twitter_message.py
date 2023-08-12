import logging
from datetime import timedelta
from typing import List

from discord_webhook import DiscordEmbed

from packages import config


class TwitterMessage:
    def __init__(self, content_dict: dict, original_message: str):
        self.log = logging.getLogger("discord")
        self.content_dict = content_dict
        self.original_message = original_message
        self.embeds = None

    def twitter_base_embed(self, is_base=False) -> DiscordEmbed:
        embed = DiscordEmbed(url=self.content_dict["tweet_url"])
        if is_base:
            embed.set_color(0x1DA1F2)
            # Set author
            embed.set_author(
                name="{} (@{})".format(
                    self.content_dict["user_nick"], self.content_dict["user_name"]
                ),
                url=self.content_dict["user_url"],
                icon_url=self.content_dict["user_image"],
            )
            # Set content
            embed.set_description(self.content_dict["content"] or "")
            # Set media info
            if self.content_dict["likes"] > 0:
                embed.add_embed_field(
                    name="Likes", value=self.content_dict["likes"], inline=True
                )
            if self.content_dict["retweets"] > 0:
                embed.add_embed_field(
                    name="Retweets", value=self.content_dict["retweets"], inline=True
                )
            # Set footer
            embed.set_footer(
                text="X",
                #proxy_icon_url="https://images-ext-1.discordapp.net/external/bXJWV2Y_F3XSra_kEqIYXAAsI3m1meckfLhYuWzxIfI/https/abs.twimg.com/icons/apple-touch-icon-192x192.png",
                icon_url="https://abs.twimg.com/responsive-web/client-web/icon-ios.77d25eba.png",
            )
            # Set timestamp
            shifted_date = self.content_dict["date"] + timedelta(
                hours=config.TIMEZONE_OFFSET
            )
            embed.set_timestamp(shifted_date.timestamp())

        return embed

    def build_url_message(self) -> List[DiscordEmbed]:
        embed = DiscordEmbed(url=self.content_dict["tweet_url"])
        return []

    def build_text_message(self) -> List[DiscordEmbed]:
        embed_list = []
        embed = self.twitter_base_embed(is_base=True)
        embed_list.append(embed)
        return embed_list

    def build_image_message(self) -> List[DiscordEmbed]:
        if not self.content_dict["media"]:
            self.log.warning("No images found")
            return None

        embed_list = []
        image_count = len(self.content_dict["media"])
        for img in range(image_count):
            if img == 0:
                embed = self.twitter_base_embed(is_base=True)
            else:
                embed = self.twitter_base_embed(is_base=False)

            # for multiple images, discord requires a new embed for each image
            embed.set_image(url=self.content_dict["media"][img])
            embed_list.append(embed)
        return embed_list

    def build_video_message(self) -> List[DiscordEmbed]:
        if not self.content_dict["media"]:
            self.log.warning("No video found")
            return None

        embed_list = []
        embed = self.twitter_base_embed(is_base=True)
        embed.set_video(url=self.content_dict["media"][0])
        embed_list.append(embed)
        return embed_list

    def build_message(self) -> bool:
        if not self.content_dict["is_fallback"] and not all(
            [
                self.content_dict["tweet_url"],
                self.content_dict["user_nick"],
                self.content_dict["user_name"],
                self.content_dict["user_url"],
                self.content_dict["user_image"],
                self.content_dict["likes"] or self.content_dict["likes"] == 0,
                self.content_dict["retweets"] or self.content_dict["retweets"] == 0,
                self.content_dict["date"],
            ]
        ):
            self.log.warning("Not all required fields are present")
            return None
        # Check if is a fallback message
        elif self.content_dict["is_fallback"]:
            self.embeds = self.build_url_message()
            return True

        if self.content_dict["is_video"]:
            self.embeds = self.build_video_message()
        elif self.content_dict["is_image"]:
            self.embeds = self.build_image_message()
        else:  # text message
            self.embeds = self.build_text_message()

        if self.embeds:
            return True
        else:
            return False
