from random import choice

import discord
from discord import option
from discord.ext import commands
from pixivpy3.utils import ParsedJson

from cogs.pixiv_utils import PixivUtils


class Pixiv(commands.Cog):
    def __init__(self, bot, refresh_token, image_directory):
        self.bot = bot
        self.utils = PixivUtils(refresh_token=refresh_token)
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
        illust = self.utils.search_illust(
            word=query,
            search_target=search_target,
            duration=duration
        )
        if not illust:
            await ctx.respond(choice([
                "靠嫩娘，妹搜着",
                "你的xp意思有点超前了",
                "没活了"
            ]))
            return
        await ctx.defer()
        await self.send_pixiv(ctx, illust=illust, msg=f"{ctx.user.mention} searched `{query}`:\n")

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

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.utils.save_history()

    async def send_pixiv(
            self,
            interaction: discord.ApplicationContext | discord.Interaction,
            illust: ParsedJson,
            page: int = 0,
            msg: str = ''
    ):
        urls = self.utils.parse_image_urls(illust, page=page)
        file = self.utils.download(urls, self.image_directory)
        with open(file, "rb") as f:
            file = discord.File(f)
            msg += f"**{illust.title}** by **{illust.user.name}**"
            msg += f" [{page + 1}/{len(illust.meta_pages)}]" if not illust.meta_single_page else ''
            await interaction.followup.send(msg, file=file, view=IllustView(self, illust, page))


class TagButton(discord.ui.Button):
    def __init__(self, pixiv: Pixiv, tag: str, row: int):
        super().__init__(label=tag, row=row)
        self.pixiv = pixiv

    async def callback(self, interaction: discord.Interaction):
        illust = self.pixiv.utils.search_illust(
            word=self.label,
            search_target='exact_match_for_tags'
        )
        await interaction.response.defer()
        await self.pixiv.send_pixiv(interaction, illust=illust,
                                 msg=f"{interaction.user.mention} clicked on `{self.label}`:\n")


class ArtistButton(discord.ui.Button):
    def __init__(self, pixiv: Pixiv, artist: str, row: int = 0):
        super().__init__(label=artist, style=discord.ButtonStyle.primary, emoji='🎨', row=row)
        self.pixiv = pixiv
        self.artist = artist

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"作者是{self.artist}")


class NextButton(discord.ui.Button):
    def __init__(self, pixiv: Pixiv, illust_id: str, page: int, row: int = 0):
        super().__init__(label='Next', style=discord.ButtonStyle.primary, emoji='▶️', row=row)
        self.pixiv = pixiv
        self.illust_id = illust_id
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        illust = self.pixiv.utils.illust_detail(self.illust_id)
        await interaction.response.defer()
        await self.pixiv.send_pixiv(interaction, illust=illust, page=self.page,
                                 msg=f"{interaction.user.mention} clicked on `{self.label}`:\n")


class IllustView(discord.ui.View):
    def __init__(self, pixiv: Pixiv, illust: ParsedJson, page: int):
        super().__init__(timeout=None)
        self.add_item(ArtistButton(pixiv, artist=illust.user.name))
        if not illust.meta_single_page and page < len(illust.meta_pages) - 1:
            self.add_item(NextButton(pixiv, illust_id=illust.id, page=page + 1))
        for i, tag in enumerate(illust.tags):
            self.add_item(TagButton(pixiv, tag=tag.name, row=i // 5 + 1))
