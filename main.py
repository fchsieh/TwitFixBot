import fixbot_init

if __name__ == "__main__":
    GLOBAL, DISCORD_CLI = fixbot_init.init()

    DISCORD_CLI.run(GLOBAL.DISCORD_TOKEN)
