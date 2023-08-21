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
        dice = [Dice.Die(side) for _ in range(number)]
        _ = map(lambda x: x.roll, dice)
        dice_str = '\n'.join(map(str, dice))
        await ctx.respond(f"{ctx.user.mention} rolled `{number}d{side}`\n"
                          f"Result: \n"
                          f"```\n"
                          f"{dice_str}"
                          f"```")

    class Die:
        def __init__(self, side: int):
            self.side = side
            self.face = None

        def roll(self) -> int:
            self.face = random.randint(1, self.side)
            return self.face

        def __str__(self) -> str:
            face = str(self.face) if self.face else '?'
            result = (f"+{'-' * (len(face) + 2)}+\n"
                      f"| {face} |\n"
                      f"+{'-' * (len(face) + 2)}+\n")
            return result
