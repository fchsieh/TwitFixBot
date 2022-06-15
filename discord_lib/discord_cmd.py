import json

import discord
from discord_webhook import DiscordWebhook


async def handle_cmd(Bot, msg_list, message):
    if msg_list[0].startswith("#"):
        cmd = msg_list[0][1:]
        if cmd == "help":
            await Bot.print_help(message.channel)

        elif cmd == "set_avatar":
            Bot.LOGGER.info(
                "User {} changed webhook avatar to {}.".format(
                    message.author, msg_list[1]
                )
            )
            Bot.WEBHOOK_AVATAR_URL = msg_list[1]
            await message.channel.send(
                "> Changed webhook avatar to <%s>" % Bot.WEBHOOK_AVATAR_URL
            )

        elif cmd == "set_name":
            Bot.LOGGER.info(
                "User {} changed webhook name from {} to {}".format(
                    message.author, Bot.WEBHOOK_NAME, msg_list[1]
                )
            )
            Bot.WEBHOOK_NAME = msg_list[1]
            await message.channel.send("> Changed webhook name to " + Bot.WEBHOOK_NAME)
            # Change now playing
            await Bot.change_presence(activity=discord.Game(Bot.WEBHOOK_NAME))

        elif cmd == "get_avatar":
            if Bot.WEBHOOK_AVATAR_URL:
                await message.channel.send(
                    "> Current webhook avatar is " + Bot.WEBHOOK_AVATAR_URL
                )
            else:
                await message.channel.send("> Current webhook avatar is default image")

        elif cmd == "get_name":
            if Bot.WEBHOOK_NAME:
                await message.channel.send(
                    "> Current webhook name is " + Bot.WEBHOOK_NAME
                )
            else:
                # using default webhook name
                await message.channel.send("> Current webhook name is " + Bot.BOT_NAME)

        elif cmd == "bind":
            if len(msg_list) != 3:
                await message.channel.send(
                    "> Usage: #bind <server_name> <channel_name>"
                )
            else:
                server_name = msg_list[1]
                channel_name = msg_list[2]
                # write to cache.json
                bind_channel = None
                bind_server = None
                for joined_server in Bot.guilds:
                    if joined_server.name == server_name:
                        for channel in joined_server.channels:
                            if channel.name == channel_name:
                                await message.channel.send(
                                    "> Successfully bound to `{}` `{}`".format(
                                        server_name, channel_name
                                    )
                                )
                                bind_server = joined_server
                                bind_channel = channel
                                break
                if bind_server and bind_channel:
                    # write to cache.json
                    with open(".cache.json", "r") as f:
                        cache = json.load(f)
                    userid = str(message.author.id)
                    if userid not in cache:
                        cache[userid] = {
                            "bind_channel": None,
                            "anon": False,
                            "bind_info": {},
                        }

                    cache[userid]["bind_channel"] = bind_channel.id
                    cache[userid]["bind_info"]["bind_server"] = bind_server.name
                    cache[userid]["bind_info"]["bind_channel"] = bind_channel.name

                    with open(".cache.json", "w") as f:
                        json.dump(cache, f)
                else:
                    await message.channel.send(
                        "> Failed to bind to `{}` `{}`, server/channel not found".format(
                            server_name, channel_name
                        )
                    )

        elif cmd == "set_anon":
            # check if user had set bind_channel
            with open(".cache.json", "r") as f:
                cache = json.load(f)
            userid = str(message.author.id)
            if userid not in cache:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return
            if cache[userid]["anon"]:
                await message.channel.send("> You are already anonymous!")
                return
            if not cache[userid]["bind_channel"]:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return

            cache[userid]["anon"] = True
            # write to cache.json
            with open(".cache.json", "w") as f:
                json.dump(cache, f)
            await message.channel.send("> You are now anonymous")

        elif cmd == "disable_anon":
            # check if user is anonymous
            with open(".cache.json", "r") as f:
                cache = json.load(f)
            userid = str(message.author.id)
            if userid not in cache:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return
            if not cache[userid]["anon"]:
                await message.channel.send("> You are already not anonymous!")
                return
            cache[userid]["anon"] = False
            # write to cache.json
            with open(".cache.json", "w") as f:
                json.dump(cache, f)
            await message.channel.send("> You are now not anonymous")

        elif cmd == "get_anon":
            # return user's current anonymous status
            with open(".cache.json", "r") as f:
                cache = json.load(f)
            userid = str(message.author.id)
            if userid not in cache:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return
            if cache[userid]["anon"]:
                await message.channel.send(
                    "> You are currently anonymous and is bound to `{}` `{}`".format(
                        cache[userid]["bind_info"]["bind_server"],
                        cache[userid]["bind_info"]["bind_channel"],
                    )
                )
            else:
                await message.channel.send("> You are not anonymous!")

        elif cmd == "get_bind":
            # return user's current bind channel
            with open(".cache.json", "r") as f:
                cache = json.load(f)
            userid = str(message.author.id)
            if userid not in cache:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return
            # return user's current bind server and channel name
            if cache[userid]["bind_info"]:
                if (
                    cache[userid]["bind_info"]["bind_server"]
                    and cache[userid]["bind_info"]["bind_channel"]
                ):
                    await message.channel.send(
                        "> You are currently bound to `{}` `{}`".format(
                            cache[userid]["bind_info"]["bind_server"],
                            cache[userid]["bind_info"]["bind_channel"],
                        )
                    )
            else:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )

        elif cmd == "unbind":
            # clear user's bind channel and server
            with open(".cache.json", "r") as f:
                cache = json.load(f)
            userid = str(message.author.id)
            if userid not in cache:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return
            if not cache[userid]["bind_channel"]:
                await message.channel.send(
                    "> You haven't bound to any channel yet, use `#bind` to bind to a channel"
                )
                return

            cache[userid]["bind_channel"] = None
            cache[userid]["bind_info"] = {}
            cache[userid]["anon"] = False

            # write to cache.json
            with open(".cache.json", "w") as f:
                json.dump(cache, f)
            await message.channel.send("> You are now unbound to any channel")

        else:
            await Bot.fun(message.channel)


async def get_anon_webhook(Bot, userid):
    # read user's bind channel id
    with open(".cache.json", "r") as f:
        cache = json.load(f)
    if userid not in cache:
        return None
    if not cache[userid]["bind_channel"]:
        return None
    channelid = cache[userid]["bind_channel"]
    # get channel by channel id
    channel = Bot.get_channel(channelid)
    if not channel:
        return None

    # Create a new webhook if it doesn't exist
    channel_all_webhooks = await channel.webhooks()
    send_webhook = None  # this is used for getting webhook url (for later usage)
    if len(channel_all_webhooks) == 0:
        # create webhook for twitter-fix bot
        send_webhook = await channel.create_webhook(
            name=Bot.BOT_NAME, avatar=Bot.WEBHOOK_AVATAR
        )
    else:
        send_webhook = discord.utils.get(channel_all_webhooks, name=Bot.BOT_NAME)
        if send_webhook is None:
            # need to create a new webhook for this app
            send_webhook = await channel.create_webhook(
                name=Bot.BOT_NAME, avatar=Bot.WEBHOOK_AVATAR
            )

    webhook_url = send_webhook.url
    if send_webhook is None or webhook_url is None:
        Bot.LOGGER.error("Failed to fetch webhook")
        return

    webhook = DiscordWebhook(
        url=webhook_url,
        rate_limit_retry=True,
        username=Bot.WEBHOOK_NAME,
        avatar_url=Bot.WEBHOOK_AVATAR_URL,
    )

    return webhook


async def anonymous_message(Bot, msg_list, message):
    # check if user is anonymous
    with open(".cache.json", "r") as f:
        cache = json.load(f)
    userid = str(message.author.id)
    # User's binding channel not found, return
    if userid not in cache:
        await Bot.fun(message.channel)
        return
    if not cache[userid]["anon"]:
        await Bot.fun(message.channel)
        return

    # Start anonymously sending message
    anon_webhook = await get_anon_webhook(Bot, userid)

    normal_message = []

    for msg in msg_list:
        valid_url = Bot.is_valid_url(msg)
        if valid_url is not None and valid_url["Twitter"]:
            # Anonymous send tweet to webhook
            await Bot.handle_twitter_message(
                valid_url["Twitter"], message, normal_message, webhook=anon_webhook
            )
        else:
            # Not a valid twitter url, skipping
            normal_message.append(msg)
            continue

    # normal message that do not require processing
    for msg in normal_message:
        await Bot.handle_normal_message(message, msg, webhook=anon_webhook)
