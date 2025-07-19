import json
import random
from typing import Optional, Dict

import discord
from discord.ext import commands
from openai import AsyncOpenAI


class Chat(commands.Cog):
    MAX_MESSAGE_LENGTH = 2000

    def __init__(self, bot, api_key):
        self.bot = bot
        self.history: Dict[int, str] = dict()
        self.vision_history: Dict[int, str] = dict()

        self.response_probability = 0.1
        self.ignored_channels = set()

        self.client = AsyncOpenAI(
            api_key=api_key
        )

        self.model = 'gpt-4o-mini'

        print("Loaded cog Chat")

    @discord.slash_command(
        name="chat",
        description="Chat with ChatGPT (GPT-4)"
    )
    @discord.option("message", required=True)
    async def chat(
            self,
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
        completion = await self.client.chat.completions.create(model=self.model, messages=messages)
        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        message: Optional[discord.WebhookMessage] = await ctx.followup.send(response)
        self.history[message.id] = json.dumps(messages)

    @commands.Cog.listener()
    async def on_message(
            self,
            message: discord.Message
    ):
        print(message.content)
        if message.author.bot:
            return
        
        if message.reference and message.reference.message_id in self.history:
            messages = json.loads(self.history[message.reference.message_id])
            if len(messages) == 1 and messages[0]['content'][0]['type'] == 'image_url':
                messages[0]['content'].insert(0, {'type': 'text', 'text': message.content})
            else:
                messages.append({"role": "user", "content": message.content})
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000
            )
            response = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": response})

            for i in range(0, len(response), Chat.MAX_MESSAGE_LENGTH):
                reply = await message.reply(response[i:i + Chat.MAX_MESSAGE_LENGTH])
                self.history[reply.id] = json.dumps(messages)
            return
        
        if message.channel.id not in self.ignored_channels and random.random() < self.response_probability:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "Please attack the following user based on their message, in their language. Be sure to try your best humiliate them and use the worst of language possible. Be creative and sarcastic."
                    },
                    {
                        "role": "user",
                        "content": message.content
                    }
                ]
                completion = await self.client.chat.completions.create(model=self.model, messages=messages)
                response = completion.choices[0].message.content
                messages.append({"role": "assistant", "content": response})

                for i in range(0, len(response), Chat.MAX_MESSAGE_LENGTH):
                    reply = await message.reply(response[i:i + Chat.MAX_MESSAGE_LENGTH])
                    self.history[reply.id] = json.dumps(messages)
            except Exception as e:
                print(f"Error processing message: {e}")

    @discord.message_command(name='Describe Image')
    async def describe_image(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Message
    ):
        await ctx.defer()

        reply = await ctx.followup.send(f"Reply to this message to ask about this image: {message.jump_url}")

        content = []
        for attachment in message.attachments:
            content.append(
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': attachment.url,
                        'detail': 'high'
                    }
                }
            )
        self.history[reply.id] = json.dumps([{'role': 'user', 'content': content}])

    @discord.slash_command(name="set_response_rate", description="Set the probability of random responses")
    @discord.default_permissions(manage_guild=True)
    @discord.option(
        "probability",
        description="Response probability (0.0 to 1.0)",
        required=True,
        min_value=0.0,
        max_value=1.0
    )
    async def set_response_rate(
        self, 
        ctx: discord.ApplicationContext,
        probability: float
    ):
        """Set the probability of random responses (0.0 to 1.0)"""
        self.response_probability = probability
        await ctx.respond(f"Response probability set to {probability:.2%}", ephemeral=True)

    @discord.slash_command(name="ignore_channel", description="Ignore a channel")
    @discord.default_permissions(manage_guild=True)
    @discord.option("channel", discord.TextChannel, description="Channel to ignore", required=False)
    async def ignore_channel(
        self, 
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel
    ):
        """Ignore a channel"""
        channel = channel or ctx.channel
        if channel.id in self.ignored_channels:
            await ctx.respond(f"{channel.mention} is already ignored", ephemeral=True)
        else:
            self.ignored_channels.add(channel.id)
            await ctx.respond(f"Now ignoring {channel.mention}", ephemeral=True)

    @discord.slash_command(name="unignore_channel", description="Unignore a channel")
    @discord.default_permissions(manage_guild=True)
    @discord.option("channel", discord.TextChannel, description="Channel to unignore", required=False)
    async def unignore_channel(
        self, 
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel
    ):
        """Unignore a channel"""
        channel = channel or ctx.channel
        if channel.id in self.ignored_channels:
            self.ignored_channels.discard(channel.id)
            await ctx.respond(f"No longer ignoring {channel.mention}", ephemeral=True)
        else:
            await ctx.respond(f"{channel.mention} is not being ignored", ephemeral=True)

    @discord.slash_command(name="response_status", description="Show current response settings")
    async def response_status(self, ctx: discord.ApplicationContext):
        """Show current response settings"""
        embed = discord.Embed(title="Random Responder Status", color=0x00ff00)
        embed.add_field(name="Response Rate", value=f"{self.response_probability:.2%}", inline=True)
        embed.add_field(name="Ignored Channels", value=f"{len(self.ignored_channels)}", inline=True)
        await ctx.respond(embed=embed)