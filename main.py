import config

if __name__ == "__main__":
    GLOBAL, DISCORD_CLI = config.init()

    DISCORD_CLI.run(GLOBAL.DISCORD_TOKEN)
