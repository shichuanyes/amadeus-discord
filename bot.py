import json
import os
from random import choice
from typing import List, Dict

import discord
from discord import option
from discord.ext import commands
from pixivpy_async import AppPixivAPI

CONFIG_NAME: str = "config.json"

TOKEN: str = ""
REFRESH_TOKEN: str = ""

api = AppPixivAPI()
bot = discord.Bot()


@bot.event
async def on_ready():
    await api.login(refresh_token=REFRESH_TOKEN)
    print(f"We have logged in as {bot.user}")


@bot.slash_command()
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    await ctx.respond("Logging out...")
    await bot.close()


@bot.slash_command(
    name="pixiv",
    description="Get'em hentais"
)
@option("query", description="Enter your query", required=True)
@option("duration", description="Duration of the images",
        choices=["within_last_day", "within_last_week", "within_last_month"], required=False)
@commands.cooldown(3, 10, commands.BucketType.user)
@commands.is_nsfw()
async def pixiv(
        ctx: discord.ApplicationContext,
        query: str,
        duration: str
):
    # Search for images based on the query
    search_result = await api.search_illust(query, sort='popular_desc', duration=duration)

    if search_result.illusts and len(search_result.illusts) > 0:
        # Get the first image from the search result
        illust = choice(search_result.illusts)

        fname = "{}.webp".format(illust.id)
        # Download the image to a local file
        await api.download(illust.image_urls.large, fname=fname)

        # Send the image to the Discord channel
        with open(fname, "rb") as f:
            file = discord.File(f)
            await ctx.respond(file=file)

        # Delete the local file
        os.remove(fname)
    else:
        await ctx.respond(choice([
            "靠嫩娘，妹搜着",
            "你的xp意思有点超前了",
            "没活了"
        ]))


@bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond("转CD中")
    else:
        raise error


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

    bot.run(TOKEN)

    with open(CONFIG_NAME, 'w+') as f:
        json.dump(config, f)
