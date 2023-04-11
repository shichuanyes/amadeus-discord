import json
from typing import Dict

import discord
from discord.ext import commands

from cogs.chat import Chat
from cogs.pixiv import Pixiv

CONFIG_NAME: str = "config.json"

TOKEN: str = ""
REFRESH_TOKEN: str = ""
API_KEY: str = ""

bot = discord.Bot()


@bot.event
async def on_connect():
    bot.add_cog(Pixiv(bot, REFRESH_TOKEN))
    bot.add_cog(Chat(bot, API_KEY))
    await bot.sync_commands()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.slash_command()
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    await ctx.respond("Logging out...")
    await bot.close()


if __name__ == "__main__":
    config: Dict = {}
    try:
        with open(CONFIG_NAME, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        with open(CONFIG_NAME, 'w+') as f:
            f.write("{}")
            f.seek(0)
            config = json.load(f)

    if "token" not in config or len(config['token']) == 0:
        config['token'] = input("Bot token not found! Please input bot token: ")
    TOKEN = config["token"]
    if "refreshToken" not in config or len(config['refreshToken']) == 0:
        config["refreshToken"] = input("Refresh token not found! Please input refresh token: ")
    REFRESH_TOKEN = config["refreshToken"]
    if "apiKey" not in config or len(config['apiKey']) == 0:
        config["apiKey"] = input("OpenAI API key not found! Please input API key: ")
    API_KEY = config["apiKey"]

    bot.run(TOKEN)

    with open(CONFIG_NAME, 'w+') as f:
        json.dump(config, f)
