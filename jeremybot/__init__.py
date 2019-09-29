import asyncio
import os

import discord
import pickledb

# TODO: probably should use sqlite3 here to be able to deal with multiple guilds for single bot
db = pickledb.load('example.db', False)
db.set("admins", "ruckusmaker")


class MyClient(discord.Client):
    # TODO: define prefix to triggering bot

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        # TODO: only accept messages from admins
        print('Message from {0.author}: {0.content}'.format(message))

    async def spam_message(self):
        # TODO: wait for on_ready event before continuing
        await asyncio.sleep(3)
        print(self.guilds)
        print(self.guilds[0].channels)
        while True:
            guild = self.guilds[0]
            channel = guild.channels[1]
            await channel.send("test")
            # TODO: download image from url and send
            # TODO: have local cache for image
            # TODO: make sleep periodic configurable by user admin
            await asyncio.sleep(5)


client = MyClient()
client.loop.create_task(client.spam_message())
client.run(os.getenv("DISCORD_TOKEN"))

# how to add timer to event loop
