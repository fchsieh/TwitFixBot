import logging
import os
from typing import List

import discord
import discord_webhook
from discord_webhook import DiscordEmbed

DISCORD_HIDE_PREFIX = r"""||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​|||||||||||| 
"""  # for hiding video link in discord message


class DiscordWebhook:
    def __init__(self):
        self.log = logging.getLogger("discord")
        # For creating webhooks
        self.BOT_NAME = ""
        self.BOT_AVATAR = None
        self._config_init()

    def _config_init(self):
        if os.getenv("BOT_NAME"):
            self.BOT_NAME = os.getenv("BOT_NAME")
        if not self.BOT_AVATAR:
            # read from file
            self.BOT_AVATAR = open(os.path.join("assets", "avatar.jpg"), "rb").read()

    async def _get_channel_webhook(
        self, message: discord.Message, channel: discord.TextChannel
    ) -> discord_webhook.DiscordWebhook:
        channel_webhooks = await channel.webhooks()
        self.send_webhook = None  # type: discord_webhook.DiscordWebhook
        for hook in channel_webhooks:
            if hook.name == self.BOT_NAME:
                self.send_webhook = hook
                break

        if self.send_webhook is None:
            self.send_webhook = await channel.create_webhook(
                name=self.BOT_NAME, avatar=self.BOT_AVATAR
            )
            if self.send_webhook is None:
                self.log.error("Failed to create webhook")
                return None

        webhook_url = self.send_webhook.url
        if webhook_url is None:
            self.log.error("Failed to get webhook url")
            return None

        message_author = message.author
        message_avatar = str(message_author.avatar)
        message_author_name = str(message_author.display_name)

        webhook = discord_webhook.DiscordWebhook(
            url=webhook_url,
            rate_limit_retry=True,
            username=message_author_name,
            avatar_url=message_avatar if message_avatar else self.BOT_AVATAR,
        )
        return webhook

    async def execute_webhook(
        self,
        original_message: str,
        message: discord.Message,
        channel: discord.TextChannel,
        embeds: List[DiscordEmbed],
    ):
        webhook = await self._get_channel_webhook(message, channel)
        if webhook is None:
            self.log.error(f"Failed to get webhook from channel '{channel.name}'")
            return

        # use original message as channel message
        webhook.set_content(original_message)

        # add embeds
        for embed in embeds:
            webhook.add_embed(embed)

        # send webhook
        sent_webhook = webhook.execute()
        if sent_webhook.status_code not in {200, 204}:
            self.log.error(f"Failed to send webhook: {sent_webhook.status_code}")
        else:
            self.log.info(f"Successfully sent webhook to '{channel.name}'")

        # if embed has video, send video separately
        webhook.remove_embeds()
        for embed in embeds:
            if embed.video:
                video_url = embed.video.get("url")
                if video_url:
                    webhook.set_content(
                        "__{} {} __".format(DISCORD_HIDE_PREFIX, video_url)
                    )
                    sent_webhook = webhook.execute()
                    if sent_webhook.status_code not in {200, 204}:
                        self.log.error(
                            f"Failed to send video link: {sent_webhook.status_code}"
                        )
                    else:
                        self.log.info(
                            f"Successfully sent video link to '{channel.name}'"
                        )
                else:
                    self.log.error("Failed to get video url from embed")
