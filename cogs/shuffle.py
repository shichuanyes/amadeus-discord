import random

import discord
from discord.ext import commands


class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="shuffle",
        description="Assign a random order to members in the current voice channel",
    )
    async def shuffle(self, ctx: discord.ApplicationContext):
        if not ctx.user.voice:
            await ctx.respond("You are not connected to a voice channel.")
            return
        members = ctx.user.voice.channel.members
        indices = list(range(len(members)))
        random.shuffle(indices)
        await ctx.respond(''.join(f"{i + 1}. {members[idx].mention}\n" for i, idx in enumerate(indices)))
