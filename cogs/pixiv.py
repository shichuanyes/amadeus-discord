from random import choice
from typing import List

import discord
from discord import option
from discord.ext import commands

from cogs.pixiv_utils import Pixiv


class PixivCog(commands.Cog):
    def __init__(self, bot, refresh_token, image_directory):
        self.bot = bot
        self.pixiv = Pixiv(refresh_token=refresh_token)
        self.image_directory = image_directory

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
        await self.send_pixiv(interaction=ctx, word=query, search_target=search_target, duration=duration)

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

    async def send_pixiv(
            self,
            interaction: discord.ApplicationContext | discord.Interaction,
            word: str,
            search_target: str = "partial_match_for_tags",
            duration: str = None
    ):
        illust = self.pixiv.search_illust(
            word=word,
            search_target=search_target,
            duration=duration
        )
        if not illust:
            await interaction.followup.send(choice([
                "靠嫩娘，妹搜着",
                "你的xp意思有点超前了",
                "没活了"
            ]))
        tags = [tag.name for tag in illust.tags]
        urls = self.pixiv.parse_image_urls(illust)
        file = self.pixiv.download(urls, self.image_directory)
        with open(file, "rb") as f:
            file = discord.File(f)
            msg = f"{interaction.user.mention} searched `{word}`:\n" \
                  f"**{illust.title}** by **{illust.user.name}**"
            await interaction.followup.send(msg, file=file, view=IllustView(self, tags, illust.user.name))


class TagButton(discord.ui.Button):
    def __init__(self, pc: PixivCog, tag: str):
        super().__init__(label=tag)
        self.pc = pc

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.pc.send_pixiv(interaction, self.label, search_target='exact_match_for_tags')


class ArtistButton(discord.ui.Button):
    def __init__(self, artist: str):
        super().__init__(label=artist, style=discord.ButtonStyle.primary, emoji='🎨')
        self.artist = artist

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"作者是{self.artist}")


class IllustView(discord.ui.View):
    def __init__(self, pc: PixivCog, tags: List[str], artist: str):
        super().__init__(timeout=None)
        self.add_item(ArtistButton(artist))
        for tag in tags:
            self.add_item(TagButton(pc, tag))
