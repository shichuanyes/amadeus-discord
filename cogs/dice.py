import random

import discord
from discord import option
from discord.ext import commands


class Dice(commands.Cog):
    CRITICAL_SUCCESS_TEXT: str = "***CRITICAL SUCCESS***"
    CRITICAL_FAILURE_TEXT: str = "***CRITICAL FAILURE***"
    SUCCESS_TEXT: str = "***SUCCESS***"
    FAILURE_TEXT: str = "***FAILURE***"

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
        for die in dice:
            die.roll()
        dice_str = '\n'.join(map(str, dice))
        await ctx.respond(f"{ctx.user.mention} rolled `{number}d{side}`\n"
                          f"Result: \n"
                          f"```\n"
                          f"{dice_str}"
                          f"```")

    @discord.slash_command(
        name="check",
        description="Check"
    )
    @option("dc", description="Difficulty class", required=False, input_type=int, min_value=1, default=10)
    @option("side", description="Number of sides", required=False, input_type=int, min_value=1, default=20)
    @option(
        "enable_critical",
        description="Enable critical success/failure",
        required=False,
        input_type=bool,
        default=True
    )
    async def dc(
            self,
            ctx: discord.ApplicationContext,
            dc: int,
            side: int,
            enable_critical: bool
    ):
        die = Dice.Die(side)
        roll = die.roll()

        result = self.SUCCESS_TEXT if roll >= dc else self.FAILURE_TEXT
        if enable_critical:
            result = self.CRITICAL_SUCCESS_TEXT if roll == side else self.CRITICAL_FAILURE_TEXT if roll == 1 else result

        await ctx.respond(f"Difficulty Class: {dc}\n"
                          f"```\n"
                          f"{die}"
                          f"```\n"
                          f"{result}")

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
