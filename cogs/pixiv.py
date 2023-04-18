import os
import time
from collections import deque
from random import choice
from typing import List, Callable

import discord
from discord import option
from discord.ext import commands
from pixivpy3 import AppPixivAPI


class Pixiv(commands.Cog):
    EXPIRATION_TIME = 3600
    IMAGE_HISTORY_SIZE = 100
    FILE_SIZE_LIMIT = 8e6
    REFRESH_TOKEN = None

    def __init__(self, bot, refresh_token):
        Pixiv.REFRESH_TOKEN = refresh_token

        self.bot = bot

        self.api = AppPixivAPI()
        self.api.auth(refresh_token=Pixiv.REFRESH_TOKEN)
        self.last_auth = int(time.time())

        self.history = deque(maxlen=self.IMAGE_HISTORY_SIZE)

        print("Loaded cog Pixiv")

    @discord.slash_command(
        name="pixiv",
        description="Get'em hentais"
    )
    @option("query", description="Enter your query", required=True)
    @option("search_target", description="Matching strategy", default="partial_match_for_tags",
            choices=["partial_match_for_tags", "exact_match_for_tags", "title_and_caption", "keyword"], required=False)
    @option("duration", description="Duration of the images",
            choices=["within_last_day", "within_last_week", "within_last_month"], required=False)
    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.is_nsfw()
    async def pixiv(
            self,
            ctx: discord.ApplicationContext,
            query: str,
            search_target: str,
            duration: str
    ):
        await ctx.defer()
        await send_pixiv(
            pixiv=self,
            target=ctx,
            query=query,
            search_target=search_target,
            duration=duration
        )

    @commands.Cog.listener()
    async def on_application_command_error(
            self,
            ctx: discord.ApplicationContext,
            error: discord.DiscordException
    ):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("转CD中")
        elif isinstance(error, discord.errors.HTTPException) and "Payload Too Large" in str(error):
            await ctx.respond("我穷蛆发不了8mb以上sad")
        else:
            raise error


class TagButton(discord.ui.Button):
    def __init__(self, tag: str, pixiv: Pixiv):
        super().__init__(label=tag)
        self.pixiv = pixiv

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await send_pixiv(
            pixiv=self.pixiv,
            target=interaction,
            query=self.label,
            search_target="exact_match_for_tags"
        )


class ArtistButton(discord.ui.Button):
    def __init__(self, artist: str, pixiv: Pixiv):
        super().__init__(label=artist, style=discord.ButtonStyle.primary, emoji='🎨')
        self.artist = artist
        self.pixiv = pixiv

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"作者是{self.artist}")


class IllustView(discord.ui.View):
    def __init__(self, tags: List[str], artist: str, pixiv: Pixiv):
        super().__init__(timeout=None)
        self.add_item(ArtistButton(artist, pixiv))
        for tag in tags:
            self.add_item(TagButton(tag, pixiv))


async def send_pixiv(
        pixiv: Pixiv,
        target: discord.ApplicationContext | discord.Interaction,
        query: str,
        search_target: str = "",
        duration: str = None
):
    send: Callable = target.followup.send

    curr_auth = int(time.time())
    if curr_auth - pixiv.last_auth >= Pixiv.EXPIRATION_TIME:
        pixiv.api.auth(refresh_token=Pixiv.REFRESH_TOKEN)
        pixiv.last_auth = curr_auth

    search_result = pixiv.api.search_illust(query, search_target=search_target, sort='popular_desc', duration=duration)

    if search_result.illusts and len(search_result.illusts) > 0:
        illust = None
        for ill in search_result.illusts:
            if ill.id not in pixiv.history:
                illust = ill
        illust = illust if illust else search_result.illusts[0]
        pixiv.history.append(illust.id)

        tags = [tag.name for tag in illust.tags]

        # TODO: add support for multi-page work
        url = illust.meta_single_page.original_image_url if illust.meta_single_page \
            else illust.meta_pages[0].image_urls.original
        name = os.path.basename(url)
        directory = os.path.join(".", "img")
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = os.path.join(directory, name)

        pixiv.api.download(url, path=directory, replace=False)
        if os.path.getsize(file_path) > pixiv.FILE_SIZE_LIMIT:  # If image exceeds discord file limit
            name = os.path.basename(illust.image_urls.large)
            file_path = os.path.join(directory, name)
            pixiv.api.download(illust.image_urls.large, path=directory, replace=False)
        with open(file_path, "rb") as f:
            file = discord.File(f)
            msg = f"{target.user.mention} searched `{query}`:\n" \
                  f"**{illust.title}** by **{illust.user.name}**"
            await send(msg, file=file, view=IllustView(tags, illust.user.name, pixiv))
    else:
        await send(choice([
            "靠嫩娘，妹搜着",
            "你的xp意思有点超前了",
            "没活了"
        ]))
