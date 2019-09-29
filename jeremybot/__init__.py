import asyncio
import os

import discord
import requests
import pickledb

# TODO: probably should use sqlite3 here to be able to deal with multiple guilds for single bot
db = pickledb.load('example.db', False)
db.set("admins", "ruckusmaker")


IMAGE_URL = "https://picsum.photos/200"


class MyClient(discord.Client):
    # TODO: define prefix to triggering bot

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        # TODO: only accept messages from admins
        print('Message from {0.author}: {0.content}'.format(message))

    async def spam_message(self):
        # TODO: wait for on_ready event before continuing
        await self.wait_until_ready()
        print(self.guilds)
        print(self.guilds[0].channels)
        while True:
            guild = self.guilds[0]
            channel = guild.channels[1]
            img_data = requests.get(IMAGE_URL).content
            with open('image_name.jpg', 'wb') as handler:
                handler.write(img_data)
            await channel.send("test", file=discord.File(open("image_name.jpg", "rb")))
            # TODO: download image from url and send
            # TODO: have local cache for image
            # TODO: make sleep periodic configurable by user admin
            # TODO: change display name on every post
            # TODO: source display names from sqlite3
            await asyncio.sleep(5)


client = MyClient()
client.loop.create_task(client.spam_message())
client.run(os.getenv("DISCORD_TOKEN"))

# how to add timer to event loop
