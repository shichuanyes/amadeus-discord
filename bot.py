import json
import os
from random import choice
from typing import Dict

import discord
import openai
from discord import option
from discord.ext import commands
from pixivpy3 import AppPixivAPI

CONFIG_NAME: str = "config.json"

MAX_MSG_LENGTH: int = 2000

TOKEN: str = ""
REFRESH_TOKEN: str = ""
API_KEY: str = ""

api = AppPixivAPI()
bot = discord.Bot()

history: Dict[int, str] = dict()


@bot.event
async def on_ready():
    api.auth(refresh_token=REFRESH_TOKEN)
    openai.api_key = API_KEY
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
    api.auth(refresh_token=REFRESH_TOKEN)

    # Search for images based on the query
    search_result = api.search_illust(query, sort='popular_desc', duration=duration)

    if search_result.illusts and len(search_result.illusts) > 0:
        # Get the first image from the search result
        illust = choice(search_result.illusts)

        fname = "{}.png".format(illust.id)
        # Download the image to a local file
        api.download(illust.image_urls.large, fname=fname)

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


@bot.slash_command(
    name="chat",
    description="Chat with ChatGPT (GPT-4)"
)
@option("message", required=True)
async def chat(
        ctx: discord.ApplicationContext,
        message: str
):
    await ctx.defer()
    messages = [
        {
            "role": "system",
            "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible."
        },
        {
            "role": "user",
            "content": message
        }
    ]
    completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    response = completion["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": response})
    message: discord.WebhookMessage = await ctx.respond(response)
    history[message.id] = json.dumps(messages)


@bot.event
async def on_message(
        message: discord.Message
):
    if message.reference and message.reference.message_id in history:
        messages = json.loads(history[message.reference.message_id])
        messages.append({"role": "user", "content": message.content})
        completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        response = completion["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": response})

        for i in range(0, len(response), MAX_MSG_LENGTH):
            reply = await message.reply(response[i:i + MAX_MSG_LENGTH])
            history[reply.id] = json.dumps(messages)


@bot.event
async def on_application_command_error(
        ctx: discord.ApplicationContext,
        error: discord.DiscordException
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
    if "apiKey" not in config or len(config['apiKey']) == 0:
        config["apiKey"] = input("OpenAI API key not found! Please input API key: ")
    API_KEY = config["apiKey"]

    bot.run(TOKEN)

    with open(CONFIG_NAME, 'w+') as f:
        json.dump(config, f)
