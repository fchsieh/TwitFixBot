import datetime
import logging
from datetime import timedelta
from typing import List

from discord_webhook import DiscordEmbed

SERVER_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
TIMEZONE_OFFSET = (
    datetime.datetime.now(datetime.timezone.utc)
    .astimezone()
    .utcoffset()
    .total_seconds()
    / 3600
)


class TwitterMessage:
    def __init__(self, content_dict: dict, original_message: str):
        self.log = logging.getLogger("discord")
        self.content_dict = content_dict
        self.original_message = original_message
        self.embeds = None

    async def twitter_base_embed(self, is_base=False) -> DiscordEmbed:
        if not all(
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
            # Set media
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
                text="Twitter",
                proxy_icon_url="https://images-ext-1.discordapp.net/external/bXJWV2Y_F3XSra_kEqIYXAAsI3m1meckfLhYuWzxIfI/https/abs.twimg.com/icons/apple-touch-icon-192x192.png",
                icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
            )
            # Set timestamp
            shifted_date = self.content_dict["date"] + timedelta(hours=TIMEZONE_OFFSET)
            embed.set_timestamp(shifted_date.timestamp())

        return embed

    async def build_text_message(self) -> List[DiscordEmbed]:
        embed_list = []
        embed = await self.twitter_base_embed(is_base=True)
        embed_list.append(embed)
        return embed_list

    async def build_image_message(self) -> List[DiscordEmbed]:
        if not self.content_dict["media"]:
            self.log.warning("No images found")
            return None

        embed_list = []
        image_count = len(self.content_dict["media"])
        for img in range(image_count):
            if img == 0:
                embed = await self.twitter_base_embed(is_base=True)
            else:
                embed = await self.twitter_base_embed(is_base=False)

            # for multiple images, discord requires a new embed for each image
            embed.set_image(url=self.content_dict["media"][img])
            embed_list.append(embed)
        return embed_list

    async def build_video_message(self) -> List[DiscordEmbed]:
        if not self.content_dict["media"]:
            self.log.warning("No video found")
            return None

        embed_list = []
        embed = await self.twitter_base_embed(is_base=True)
        embed.set_video(url=self.content_dict["media"][0])
        embed_list.append(embed)
        return embed_list

    async def build_message(self) -> bool:
        if self.content_dict["is_video"]:
            self.embeds = await self.build_video_message()
        elif self.content_dict["is_image"]:
            self.embeds = await self.build_image_message()
        else:  # text message
            self.embeds = await self.build_text_message()

        if self.embeds:
            return True
        else:
            return False
