import random

import discord
from discord import option
from discord.ext import commands


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        print("Loaded cog Dice")

    @discord.slash_command(
        name="dice",
        description="Roll a dice, DnD style"
    )
    @option("number", description="Number of dices", required=False, input_type=int, min_value=1, default=1)
    @option("side", description="Number of sides", required=False, input_type=int, min_value=1, default=20)
    async def dice(
            self,
            ctx: discord.ApplicationContext,
            number: int,
            side: int
    ):
        dice = [random.randint(1, side) for _ in range(number)]
        await ctx.respond(f"{' + '.join(map(str, dice))} = {sum(dice)}")
