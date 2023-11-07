import json
from typing import Optional, Dict

import discord
from discord import option
from discord.ext import commands
from openai import AsyncOpenAI


class Chat(commands.Cog):
    MAX_MESSAGE_LENGTH = 2000

    def __init__(self, bot, api_key):
        self.bot = bot
        self.history: Dict[int, str] = dict()

        self.client = AsyncOpenAI(
            api_key=api_key
        )

        print("Loaded cog Chat")

    @discord.slash_command(
        name="chat",
        description="Chat with ChatGPT (GPT-4)"
    )
    @option("message", required=True)
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
        completion = await self.client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        message: Optional[discord.WebhookMessage] = await ctx.followup.send(response)
        self.history[message.id] = json.dumps(messages)

    @commands.Cog.listener()
    async def on_message(
            self,
            message: discord.Message
    ):
        if message.reference and message.reference.message_id in self.history:
            messages = json.loads(self.history[message.reference.message_id])
            messages.append({"role": "user", "content": message.content})
            completion = await self.client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
            response = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": response})

            for i in range(0, len(response), Chat.MAX_MESSAGE_LENGTH):
                reply = await message.reply(response[i:i + Chat.MAX_MESSAGE_LENGTH])
                self.history[reply.id] = json.dumps(messages)

    @discord.message_command(name='Describe Image')
    async def describe_image(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Message
    ):
        if len(message.attachments) != 1:
            await ctx.respond('别急')
            return

        await ctx.defer()

        url = message.attachments[0].url
        completion = await self.client.chat.completions.create(
            model='gpt-4-vision-preview',
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': "请描述图片"},
                        {'type': 'image_url', 'image_url': url}
                    ]
                }
            ],
            max_tokens=1000
        )

        await ctx.respond(completion.choices[0].message.content)
