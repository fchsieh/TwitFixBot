from discord_webhook import DiscordEmbed


class DiscordMessage:
    def __init__(self, content=None, logger=None):
        self.logger = logger
        self.content = content
        self.embed_list = []
        self.video = {
            "url": None,
            "thumbnail": None,
        }
        self.discord_colors = {"Twitter": 1942002}
        self.build_message()

    def twitter_embed_block(self, isBase=False):
        embed = DiscordEmbed(url=self.content["Tweet_url"])
        if isBase:
            # set basic tweet info
            embed.set_color(self.discord_colors["Twitter"])
            embed.set_description(self.content["Description"])
            embed.set_author(
                name=self.content["Author"],
                url=self.content["Author_url"],
                icon_url=self.content["Author_icon_img"],
            )
            embed.add_embed_field(
                name="Likes", value=self.content["Likes"], inline=True
            )
            embed.add_embed_field(
                name="Retweets", value=self.content["Retweets"], inline=True
            )
            embed.set_footer(
                text="Twitter",
                proxy_icon_url="https://images-ext-1.discordapp.net/external/bXJWV2Y_F3XSra_kEqIYXAAsI3m1meckfLhYuWzxIfI/https/abs.twimg.com/icons/apple-touch-icon-192x192.png",
                icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
            )
            embed.set_timestamp(timestamp=self.content["Timestamp"])

        return embed

    def build_message(self):
        type = self.content["Type"]

        if type == "Image":
            image_count = self.content["Images"][-1]
            image_list = self.content["Images"][:image_count]

            for image in range(image_count):
                if image == 0:
                    embed = self.twitter_embed_block(isBase=True)
                else:
                    embed = self.twitter_embed_block(isBase=False)

                embed.set_image(url=image_list[image])
                self.embed_list.append(embed)

        elif type == "Video":
            info = self.twitter_embed_block(isBase=True)
            self.embed_list.append(info)

            if self.content["Video_url"] is None:
                self.logger.warning("Failed to fetch video url")
            self.video["url"] = self.content["Video_url"]
            self.video["thumbnail"] = self.content["Thumbnail"]
