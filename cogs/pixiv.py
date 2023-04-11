import os
import time
from random import choice
from typing import List, Callable

import discord
from discord import option
from discord.ext import commands
from pixivpy3 import AppPixivAPI


class Pixiv(commands.Cog):
    EXPIRATION_TIME = 3600
    REFRESH_TOKEN = None

    def __init__(self, bot, refresh_token):
        Pixiv.REFRESH_TOKEN = refresh_token

        self.bot = bot
        self.api = AppPixivAPI()
        self.api.auth(refresh_token=Pixiv.REFRESH_TOKEN)
        self.last_auth = int(time.time())

        print("Loaded cog Pixiv")

    @discord.slash_command(
        name="pixiv",
        description="Get'em hentais"
    )
    @option("query", description="Enter your query", required=True)
    @option("duration", description="Duration of the images",
            choices=["within_last_day", "within_last_week", "within_last_month"], required=False)
    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.is_nsfw()
    async def pixiv(
            self,
            ctx: discord.ApplicationContext,
            query: str,
            duration: str
    ):
        await send_pixiv(pixiv=self, target=ctx, query=query, duration=duration)

    @commands.Cog.listener()
    async def on_application_command_error(
            self,
            ctx: discord.ApplicationContext,
            error: discord.DiscordException
    ):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("转CD中")
        else:
            raise error


class TagButton(discord.ui.Button):
    def __init__(self, tag: str, pixiv: Pixiv):
        super().__init__(label=tag)
        self.pixiv = pixiv

    async def callback(self, interaction: discord.Interaction):
        await send_pixiv(pixiv=self.pixiv, target=interaction, query=self.label)


class TagView(discord.ui.View):
    def __init__(self, tags: List[str], pixiv: Pixiv):
        super().__init__(timeout=None)
        for tag in tags:
            self.add_item(TagButton(tag, pixiv))


async def send_pixiv(
        pixiv: Pixiv,
        target: discord.ApplicationContext | discord.Interaction,
        query: str,
        duration: str = None
):
    send: Callable = target.respond if target is discord.ApplicationContext else target.response.send_message

    curr_auth = int(time.time())
    if curr_auth - pixiv.last_auth >= Pixiv.EXPIRATION_TIME:
        pixiv.api.auth(refresh_token=Pixiv.REFRESH_TOKEN)
        pixiv.last_auth = curr_auth

    search_result = pixiv.api.search_illust(query, sort='popular_desc', duration=duration)

    if search_result.illusts and len(search_result.illusts) > 0:
        illust = choice(search_result.illusts)

        fname = "{}.png".format(illust.id)
        tags = [tag.name for tag in illust.tags]

        pixiv.api.download(illust.image_urls.large, fname=fname)
        with open(fname, "rb") as f:
            file = discord.File(f)
            msg = f"Title: **{illust.title}**\n" \
                  f"User: **{illust.user.name}**\n" \
                  f"Tags: {', '.join(['**' + tag + '**' for tag in tags])}"
            await send(msg, file=file, view=TagView(tags, pixiv))
        os.remove(fname)
    else:
        await send(choice([
            "靠嫩娘，妹搜着",
            "你的xp意思有点超前了",
            "没活了"
        ]))
